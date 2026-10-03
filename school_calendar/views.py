from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from courses.models import Program

from .forms import AcademicEventForm, EventCategoryForm
from .models import AcademicEvent, EventCategory


def academic_calendar_view(request):
    """Affiche le calendrier interactif FullCalendar avec formulaires d'ajout (événements et catégories)."""
    if request.method == 'POST':
        # Ajout d'une catégorie
        if 'add_category' in request.POST:
            cat_form = EventCategoryForm(request.POST)
            if cat_form.is_valid():
                cat_form.save()
                messages.success(
                    request, 'Catégorie ajoutée avec succès.'
                )
            else:
                messages.error(
                    request,
                    'Erreur lors de la création de la catégorie.',
                )
            return redirect('school_calendar:calendar')

        # Ajout d'un événement
        elif 'add_event' in request.POST:
            event_form = AcademicEventForm(request.POST)
            if event_form.is_valid():
                event_form.save()
                messages.success(
                    request, 'Événement ajouté avec succès.'
                )
            else:
                messages.error(
                    request,
                    'Veuillez corriger les erreurs dans le formulaire.',
                )
            return redirect('school_calendar:calendar')

    # Filtrage des 5 prochains événements à venir à partir de maintenant
    upcoming_events = (
        AcademicEvent.objects.select_related('category')
        .filter(start_date__gte=timezone.now())
        .order_by('start_date')[:5]
    )

    # --- Grille mensuelle calculée côté serveur (sans FullCalendar/CDN) ---
    import calendar as pycalendar
    from datetime import date as dt_date, timedelta

    month_str = request.GET.get('month') or ''
    try:
        year, month = (int(x) for x in month_str.split('-'))
        first_day = dt_date(year, month, 1)
    except (ValueError, TypeError):
        today = timezone.localdate()
        first_day = today.replace(day=1)
    last_day = dt_date(
        first_day.year + (1 if first_day.month == 12 else 0),
        1 if first_day.month == 12 else first_day.month + 1,
        1,
    ) - timedelta(days=1)

    category_id = request.GET.get('category') or ''
    month_events = AcademicEvent.objects.filter(
        start_date__date__lte=last_day, end_date__date__gte=first_day
    ).select_related('category')
    if category_id:
        month_events = month_events.filter(category_id=category_id)
    events_by_day = {}
    for event in month_events:
        d = max(event.start_date.date(), first_day)
        end = min(event.end_date.date(), last_day)
        while d <= end:
            events_by_day.setdefault(d, []).append(event)
            d += timedelta(days=1)

    # Semaines du mois (lundi → dimanche)
    weeks, current = [], first_day - timedelta(days=first_day.weekday())
    today = timezone.localdate()
    while current <= last_day:
        week = []
        for _ in range(7):
            week.append({
                'date': current,
                'in_month': current.month == first_day.month,
                'is_today': current == today,
                'events': events_by_day.get(current, []),
            })
            current += timedelta(days=1)
        weeks.append(week)

    prev_month = (first_day - timedelta(days=1)).replace(day=1)
    next_month = (last_day + timedelta(days=1))
    def _qs(d):
        base = f'?month={d.year}-{d.month:02d}'
        return base + (f'&category={category_id}' if category_id else '')

    context = {
        'title': 'Calendrier Académique',
        'categories': EventCategory.objects.all(),
        'programs': Program.objects.all(),
        'upcoming_events': upcoming_events,
        'form': AcademicEventForm(),
        'cat_form': EventCategoryForm(),
        'weeks': weeks,
        'month_label': f'{pycalendar.month_name[first_day.month].capitalize()} {first_day.year}',
        'prev_url': _qs(prev_month),
        'next_url': _qs(next_month),
        'f_category': category_id,
    }
    return render(request, 'calendar/academic_calendar.html', context)


def academic_calendar_events_api(request):
    """Endpoint API JSON consommé par FullCalendar."""
    start = request.GET.get('start')
    end = request.GET.get('end')
    category_id = request.GET.get('category')
    program_id = request.GET.get('program')

    events_qs = AcademicEvent.objects.select_related('category')

    # Filtre par dates
    if start and end:
        events_qs = events_qs.filter(start_date__lte=end, end_date__gte=start)

    # Filtres optionnels
    if category_id:
        events_qs = events_qs.filter(category_id=category_id)

    if program_id:
        events_qs = events_qs.filter(programs__id=program_id)

    events_data = []
    for event in events_qs.distinct():
        start_iso = (
            event.start_date.isoformat() if event.start_date else None
        )
        end_iso = event.end_date.isoformat() if event.end_date else start_iso
        color = (
            event.category.color
            if (event.category and event.category.color)
            else '#3B82F6'
        )

        events_data.append(
            {
                'id': event.id,
                'title': event.title,
                'start': start_iso,
                'end': end_iso,
                'allDay': getattr(event, 'is_all_day', False),
                'backgroundColor': color,
                'borderColor': color,
                'extendedProps': {
                    'description': event.description or '',
                    'category': (
                        event.category.name
                        if event.category
                        else 'Général'
                    ),
                },
            }
        )

    return JsonResponse(events_data, safe=False)


def academic_calendar_list_view(request):
    """Affiche la liste complète des événements et traite l'édition via modale."""
    # Traitement de la modification envoyée depuis la modale
    if request.method == 'POST' and 'edit_event_id' in request.POST:
        event_id = request.POST.get('edit_event_id')
        event = get_object_or_404(AcademicEvent, pk=event_id)
        form = AcademicEventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Événement modifié avec succès.')
        else:
            messages.error(
                request, "Erreur lors de la modification de l'événement."
            )
        return redirect('school_calendar:calendar_list')

    category_id = request.GET.get('category')
    search_query = request.GET.get('q')

    events_qs = (
        AcademicEvent.objects.select_related('category')
        .prefetch_related('programs')
        .order_by('start_date')
    )

    if category_id:
        events_qs = events_qs.filter(category_id=category_id)

    if search_query:
        events_qs = events_qs.filter(title__icontains=search_query)

    context = {
        'title': 'Liste des Événements Académiques',
        'events': events_qs,
        'categories': EventCategory.objects.all(),
        'selected_category': category_id,
        'search_query': search_query or '',
        'now': timezone.now(),
    }
    return render(request, 'calendar/academic_calendar_list.html', context)


def academic_event_delete_view(request, pk):
    """Supprime un événement (appelé depuis la modale de suppression)."""
    event = get_object_or_404(AcademicEvent, pk=pk)
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Événement supprimé avec succès.')
    return redirect('school_calendar:calendar_list')
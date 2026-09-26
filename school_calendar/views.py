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

    context = {
        'title': 'Calendrier Académique',
        'categories': EventCategory.objects.all(),
        'programs': Program.objects.all(),
        'upcoming_events': upcoming_events,
        'form': AcademicEventForm(),
        'cat_form': EventCategoryForm(),
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
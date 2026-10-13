"""Emploi du temps : grille hebdomadaire, ajout de créneaux, export PDF."""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
from io import BytesIO
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.utils import timezone

# Modèles propres à timetable
from .models import TimeSlot, Classroom

# Modèles externes
from classes.models import Class
from courses.models import Program, ProgramSubject, Subject
from teachers.models import Teacher

# Formulaires
from .forms import TimeSlotForm, ClassroomForm

DAYS = [
    (1, 'Lundi'),
    (2, 'Mardi'),
    (3, 'Mercredi'),
    (4, 'Jeudi'),
    (5, 'Vendredi'),
    (6, 'Samedi'),
]


def _school_of(user):
    return getattr(user, 'school', None)


def timetable_view(request):
    school = _school_of(request.user)

    selected_program_id = request.GET.get('program')
    selected_class_id = request.GET.get('class')

    programs = Program.objects.all()
    classes = Class.objects.all()
    if school:
        programs = programs.filter(school=school)
        classes = classes.filter(school=school)

    # Filtrer les classes selon le programme si sélectionné
    if selected_program_id and selected_program_id.isdigit():
        classes = classes.filter(program_id=int(selected_program_id))

    selected_class = None
    timeslots = []

    if selected_class_id and selected_class_id.isdigit():
        selected_class = get_object_or_404(Class, pk=int(selected_class_id))
        timeslots = TimeSlot.objects.filter(
            school_class=selected_class
        ).select_related('subject', 'teacher', 'classroom').order_by(
            'day_of_week', 'start_time')

    # Traitement du formulaire d'ajout de cours
    # La classe « de référence » pour valider le formulaire : celle choisie
    # dans la modale (POST) ou celle de la page (GET).
    reference_class = selected_class
    if request.method == 'POST' and 'add_timeslot' in request.POST:
        posted_class = request.POST.get('school_class')
        if posted_class and posted_class.isdigit():
            reference_class = Class.objects.filter(pk=int(posted_class)).first() \
                or reference_class
        timeslot_form = TimeSlotForm(
            request.POST, selected_class=reference_class, school=school)
        if timeslot_form.is_valid():
            slot = timeslot_form.save(commit=False)
            if reference_class and not slot.school_class_id:
                slot.school_class = reference_class
            # Enseignant de la matière par défaut si non choisi
            if not slot.teacher_id and slot.subject_id:
                slot.teacher = getattr(slot.subject, 'teacher', None)
            # Isolation multi-écoles
            if school and not slot.school_class_id:
                slot.school_class = selected_class or reference_class
            slot.save()
            return redirect(request.get_full_path())
    else:
        timeslot_form = TimeSlotForm(
            selected_class=selected_class, school=school)

    # Traitement du formulaire d'ajout de salle
    if request.method == 'POST' and 'add_classroom' in request.POST:
        classroom_form = ClassroomForm(request.POST, school=school)
        if classroom_form.is_valid():
            room = classroom_form.save(commit=False)
            if school:
                room.school = school
            room.save()
            return redirect(request.get_full_path())
    else:
        classroom_form = ClassroomForm(school=school)

    context = {
        'title': 'Emploi du temps',
        'programs': programs,
        'classes': classes,
        'selected_program_id': int(selected_program_id) if selected_program_id and selected_program_id.isdigit() else None,
        'selected_class': selected_class,
        'timeslots': timeslots,
        'days': DAYS,
        'timeslot_form': timeslot_form,
        'classroom_form': classroom_form,
    }
    return render(request, 'timetable/timetable_grid.html', context)


def ajax_get_subjects_by_class(request):
    """Matières de la classe choisie (= programme de la classe), avec
    l'enseignant conseillé. Utilisé par la modale « Ajouter un cours »."""
    class_id = request.GET.get('class_id')
    subjects_data = []

    if class_id and class_id.isdigit():
        classroom = Class.objects.filter(pk=int(class_id)).first()
        if classroom and request.user.school_id and classroom.school_id != request.user.school_id:
            classroom = None
        if classroom:
            subjects = Subject.objects.none()
            if classroom.program_id:
                subjects = Subject.objects.filter(
                    subject_programs__program=classroom.program
                ).distinct()
            for sub in subjects:
                link = ProgramSubject.objects.filter(
                    program_id=classroom.program_id, subject=sub
                ).select_related('teacher').first()
                teacher = link.teacher if link else None
                subjects_data.append({
                    'id': sub.id,
                    'name': sub.name,
                    'code': getattr(sub, 'code', ''),
                    'teacher_id': teacher.id if teacher else None,
                })

    return JsonResponse({'subjects': subjects_data})


@require_POST
def timeslot_delete_view(request, pk):
    """Supprime un créneau horaire (TimeSlot)."""
    slot = get_object_or_404(TimeSlot, pk=pk)
    slot.delete()
    return redirect(request.META.get('HTTP_REFERER', '/timetable/'))


def timetable_export_pdf(request):
    """Export PDF professionnel de l'emploi du temps d'une classe (A4 paysage)."""
    school = _school_of(request.user)
    class_id = request.GET.get('class')
    classroom = get_object_or_404(Class, pk=class_id) if class_id and class_id.isdigit() else None
    if classroom is None:
        return redirect('/timetable/')

    timeslots = TimeSlot.objects.filter(
        school_class=classroom).select_related('subject', 'teacher', 'classroom')

    # Créneaux horaires uniques, triés
    ranges = sorted({(s.start_time, s.end_time) for s in timeslots})

    grid = []
    for start, end in ranges:
        row = {'label': f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}",
               'cells': []}
        for day_num, _day_name in DAYS:
            cell_items = [
                s for s in timeslots
                if s.day_of_week == day_num and s.start_time == start and s.end_time == end
            ]
            row['cells'].append(cell_items)
        grid.append(row)

    context = {
        'school': school,
        'classroom': classroom,
        'program': classroom.program,
        'days': DAYS,
        'grid': grid,
        'now': timezone.localtime(),
    }
    html = render_to_string('timetable/timetable_pdf.html', context)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode('UTF-8')), result, encoding='UTF-8')
    if pdf.err:
        return HttpResponse("Erreur lors de la génération du PDF.", status=500)
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    safe_name = classroom.name.replace(' ', '_')
    response['Content-Disposition'] = f'inline; filename="emploi_du_temps_{safe_name}.pdf"'
    return response

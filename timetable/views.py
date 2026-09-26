from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse

# 1. Modèles propres à timetable
from .models import TimeSlot, Classroom

# 2. Modèles externes avec les VRAIS noms et chemins
from classes.models import Class
from courses.models import Program, Subject

# 3. Formulaires
from .forms import TimeSlotForm, ClassroomForm


def timetable_view(request):
    selected_program_id = request.GET.get('program')
    selected_class_id = request.GET.get('class')

    programs = Program.objects.all()
    classes = Class.objects.all()

    # Filtrer les classes selon le programme si sélectionné
    if selected_program_id and selected_program_id.isdigit():
        classes = classes.filter(program_id=int(selected_program_id))

    selected_class = None
    timeslots = []

    if selected_class_id and selected_class_id.isdigit():
        selected_class = get_object_or_404(Class, pk=int(selected_class_id))
        # Optimisation SQL des requêtes pour l'affichage
        timeslots = TimeSlot.objects.filter(school_class=selected_class).select_related(
            'subject', 'teacher', 'classroom'
        )

    # Traitement du formulaire d'ajout de cours
    if request.method == 'POST' and 'add_timeslot' in request.POST:
        timeslot_form = TimeSlotForm(request.POST, class_id=selected_class_id)
        if timeslot_form.is_valid():
            slot = timeslot_form.save(commit=False)

            # Attribution de la classe filtrée si non renseignée
            if selected_class and not slot.school_class_id:
                slot.school_class = selected_class

            # Attribution automatique de l'enseignant de la matière s'il n'a pas été choisi manuellement
            if not slot.teacher and slot.subject and hasattr(slot.subject, 'teacher'):
                slot.teacher = slot.subject.teacher

            slot.save()
            return redirect(request.get_full_path())
    else:
        timeslot_form = TimeSlotForm(class_id=selected_class_id)

    # Traitement du formulaire d'ajout de salle
    if request.method == 'POST' and 'add_classroom' in request.POST:
        classroom_form = ClassroomForm(request.POST)
        if classroom_form.is_valid():
            classroom_form.save()
            return redirect(request.get_full_path())
    else:
        classroom_form = ClassroomForm()

    days = [
        (1, 'Lundi'),
        (2, 'Mardi'),
        (3, 'Mercredi'),
        (4, 'Jeudi'),
        (5, 'Vendredi'),
        (6, 'Samedi'),
    ]

    context = {
        'title': 'Emploi du temps',
        'programs': programs,
        'classes': classes,
        'selected_program_id': int(selected_program_id) if selected_program_id and selected_program_id.isdigit() else None,
        'selected_class': selected_class,
        'timeslots': timeslots,
        'days': days,
        'timeslot_form': timeslot_form,
        'classroom_form': classroom_form,
    }
    return render(request, 'timetable/timetable_grid.html', context)


def ajax_get_subjects_by_class(request):
    """Retourne la liste JSON des matières rattachées à la classe sélectionnée."""
    class_id = request.GET.get('class_id')
    subjects_data = []

    if class_id and class_id.isdigit():
        subjects = Subject.objects.filter(
            subject_programs__program__classes__id=int(class_id)
        ).distinct()

        for sub in subjects:
            teacher_id = None
            if hasattr(sub, 'teacher') and sub.teacher:
                teacher_id = sub.teacher.id

            subjects_data.append({
                'id': sub.id,
                'name': sub.name,
                'code': getattr(sub, 'code', ''),
                'teacher_id': teacher_id,
            })

    return JsonResponse({'subjects': subjects_data})

from django.views.decorators.http import require_POST

@require_POST
def timeslot_delete_view(request, pk):
    """Supprime un créneau horaire (TimeSlot)."""
    slot = get_object_or_404(TimeSlot, pk=pk)
    slot.delete()
    # Redirige l'utilisateur vers la page précédente
    return redirect(request.META.get('HTTP_REFERER', 'timetable:grid'))
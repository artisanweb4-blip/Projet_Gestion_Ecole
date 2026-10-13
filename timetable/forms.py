from django import forms
from classes.models import Class
from courses.models import Subject
from teachers.models import Teacher
from .models import TimeSlot, Classroom


class TimeSlotForm(forms.ModelForm):
    """Créneau de l'emploi du temps — source unique (timetable/forms.py).

    - Classe : uniquement les classes de l'école de l'utilisateur ;
    - Matière : uniquement les matières du PROGRAMME de la classe choisie ;
    - Enseignant : uniquement les enseignants ACTIFS de l'école, affichés
      « Nom Prénom — Spécialité » ;
    - Salle : salles de l'école.
    """
    class Meta:
        model = TimeSlot
        fields = ['school_class', 'subject', 'teacher', 'classroom', 'day_of_week', 'start_time', 'end_time']
        widgets = {
            'school_class': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'classroom': forms.Select(attrs={'class': 'form-control'}),
            'day_of_week': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

    def __init__(self, *args, selected_class=None, school=None, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. Classes de l'école
        classes_qs = Class.objects.all()
        if school:
            classes_qs = classes_qs.filter(school=school)
        self.fields['school_class'].queryset = classes_qs.order_by('name')
        self.fields['school_class'].empty_label = '— Choisir la classe —'

        # Classe de référence : passée par la vue, sinon celle du POST
        if selected_class is None and self.is_bound:
            posted = self.data.get('school_class')
            if posted and str(posted).isdigit():
                selected_class = classes_qs.filter(pk=int(posted)).first()

        # 2. Matières = programme de la classe choisie UNIQUEMENT
        if selected_class and selected_class.program_id:
            self.fields['subject'].queryset = Subject.objects.filter(
                subject_programs__program=selected_class.program
            ).distinct()
            self.fields['subject'].empty_label = '— Choisir une matière —'
        elif selected_class is not None:
            self.fields['subject'].queryset = Subject.objects.none()
            self.fields['subject'].empty_label = 'Aucun programme lié à cette classe'
        else:
            self.fields['subject'].queryset = Subject.objects.none()
            self.fields['subject'].empty_label = "— Choisissez d'abord la classe —"

        # 3. Enseignants actifs de l'école « Nom Prénom — Spécialité »
        teachers_qs = Teacher.objects.filter(is_active=True)
        if school:
            teachers_qs = teachers_qs.filter(school=school)
        self.fields['teacher'].queryset = teachers_qs.order_by('last_name', 'first_name')
        self.fields['teacher'].required = False
        self.fields['teacher'].empty_label = '— Choisir un enseignant —'
        self.fields['teacher'].label_from_instance = lambda obj: (
            f"{obj.last_name} {obj.first_name}"
            + (f' — {obj.specialization}' if obj.specialization else '')
        )

        # 4. Salles de l'école
        rooms_qs = Classroom.objects.all()
        if school:
            rooms_qs = rooms_qs.filter(school=school)
        self.fields['classroom'].queryset = rooms_qs.order_by('name')
        self.fields['classroom'].empty_label = '— Choisir une salle —'

        # 5. Libellés français
        self.fields['school_class'].label = 'Classe'
        self.fields['subject'].label = 'Matière'
        self.fields['teacher'].label = 'Enseignant'
        self.fields['classroom'].label = 'Salle'
        self.fields['day_of_week'].label = 'Jour de la semaine'
        self.fields['start_time'].label = 'Heure de début'
        self.fields['end_time'].label = 'Heure de fin'

        # 6. Pré-sélectionner la classe courante
        if selected_class:
            self.fields['school_class'].initial = selected_class


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ['name', 'capacity', 'building']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Salle A10'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 40'}),
            'building': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Bâtiment Principal'}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Nom de la salle'
        self.fields['capacity'].label = 'Capacité (places)'
        self.fields['building'].label = 'Bâtiment'
        if school:
            self.fields['building'].required = False

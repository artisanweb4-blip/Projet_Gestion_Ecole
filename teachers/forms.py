from django import forms
from courses.models import Subject
from .models import Teacher
from timetable.models import TimeSlot, Classroom  # ou le nom exact de votre app planning

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            'first_name', 
            'last_name', 
            'email', 
            'phone', 
            'specialization', 
            'hire_date', 
            'photo'
        ]
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Injection automatique de la classe CSS form-control sur tous les champs
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ['name', 'capacity', 'building']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Salle A10'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 40'}),
            'building': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Bâtiment Principal'}),
        }


class TimeSlotForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        fields = ['school_class', 'subject', 'teacher', 'classroom', 'day_of_week', 'start_time', 'end_time']
        widgets = {
            'school_class': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'classroom': forms.Select(attrs={'class': 'form-control'}),
            'day_of_week': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        selected_class = kwargs.pop('selected_class', None)
        super().__init__(*args, **kwargs)

        # 1. Charger tous les enseignants enregistrés dans la table Teacher
        self.fields['teacher'].queryset = Teacher.objects.all()

        # Format d'affichage dans la liste déroulante : "Prénom Nom (Spécialité)" si renseignée
        self.fields['teacher'].label_from_instance = lambda obj: (
            f"{obj.first_name} {obj.last_name}" + (f" ({obj.specialization})" if obj.specialization else "")
        )

        # 2. Filtrer les matières selon la classe sélectionnée
        if selected_class and hasattr(selected_class, 'program') and selected_class.program:
            self.fields['subject'].queryset = Subject.objects.filter(
                subject_programs__program=selected_class.program
            ).distinct()
        elif self.instance and self.instance.pk and self.instance.school_class and self.instance.school_class.program:
            self.fields['subject'].queryset = Subject.objects.filter(
                subject_programs__program=self.instance.school_class.program
            ).distinct()
        else:
            self.fields['subject'].queryset = Subject.objects.all()

        # 3. Pré-sélectionner la classe courante
        if selected_class:
            self.fields['school_class'].initial = selected_class
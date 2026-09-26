from django import forms
from .models import TimeSlot, Classroom
from classes.models import Class
from courses.models import Subject


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
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        class_id = kwargs.pop('class_id', None)
        super().__init__(*args, **kwargs)

        self.fields['teacher'].required = False
        self.fields['teacher'].empty_label = "-- Sélectionner un enseignant --"

        if class_id and str(class_id).isdigit():
            # Filtrer les matières associées à la classe sélectionnée via subject_programs
            self.fields['subject'].queryset = Subject.objects.filter(
                subject_programs__program__classes__id=int(class_id)
            ).distinct()
            self.fields['school_class'].initial = int(class_id)


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ['name', 'capacity', 'building']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Salle A1'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 30'}),
            'building': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Bâtiment principal'}),
        }
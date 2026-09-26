from django import forms
from .models import AcademicEvent, EventCategory


class EventCategoryForm(forms.ModelForm):

    class Meta:
        model = EventCategory
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ex: Examens, Vacances...',
                }
            ),
            'color': forms.TextInput(
                attrs={
                    'type': 'color',
                    'class': 'form-control form-control-color',
                    'style': 'height: 38px; cursor: pointer; width: 100%;',
                }
            ),
        }


class AcademicEventForm(forms.ModelForm):

    class Meta:
        model = AcademicEvent
        fields = [
            'title',
            'category',
            'programs',
            'start_date',
            'end_date',
            'is_all_day',
            'description',
        ]
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': "Titre de l'événement",
                }
            ),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'programs': forms.SelectMultiple(
                attrs={'class': 'form-control', 'style': 'height: 100px;'}
            ),
            'start_date': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'end_date': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'is_all_day': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Description optionnelle...',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Formattage automatique de la date pour le champ HTML datetime-local lors de l'édition
        if self.instance and self.instance.pk:
            if self.instance.start_date:
                self.initial['start_date'] = self.instance.start_date.strftime(
                    '%Y-%m-%dT%H:%M'
                )
            if self.instance.end_date:
                self.initial['end_date'] = self.instance.end_date.strftime(
                    '%Y-%m-%dT%H:%M'
                )
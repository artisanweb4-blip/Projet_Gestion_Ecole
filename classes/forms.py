from django import forms
from .models import Class


class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = [
            'name',
            'level',
            'program',      # 👈 Champ ajouté
            'section',
            'capacity',
            'room',
            'responsible',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: L1 - Groupe A ou 1ère A1'
            }),
            'level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'program': forms.Select(attrs={     # 👈 Widget pour le programme
                'class': 'form-select'
            }),
            'section': forms.Select(attrs={
                'class': 'form-select'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'room': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Salle 102'
            }),
            'responsible': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre le programme optionnel ou personnaliser le libellé vide
        self.fields['program'].empty_label = "Sélectionnez un programme (optionnel)"
        self.fields['responsible'].empty_label = "Sélectionnez un responsable (optionnel)"
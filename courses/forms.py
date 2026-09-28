# courses/forms.py

from django import forms
from django.forms import inlineformset_factory
from .models import Program, ProgramSubject, Subject


class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['code', 'name', 'description']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: L1-INFO'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Licence 1 Informatique'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ProgramSubjectForm(forms.ModelForm):
    # Champ de texte affiché à l'utilisateur
    subject_name = forms.CharField(
        label="Matière",
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Mathématiques'
        })
    )

    class Meta:
        model = ProgramSubject
        fields = ['subject_name', 'subject', 'teacher', 'coefficient', 'hours_per_week', 'total_hours', 'is_optional']
        widgets = {
            # On masque le ForeignKey direct
            'subject': forms.HiddenInput(),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'coefficient': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'hours_per_week': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_optional': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre le champ ForeignKey non obligatoire dans la validation initiale
        self.fields['subject'].required = False
        
        # Pré-remplir la matière en mode édition (injection dans self.initial)
        if self.instance and self.instance.pk and self.instance.subject:
            self.initial['subject_name'] = self.instance.subject.name

    def clean(self):
        cleaned_data = super().clean()
        subject_name = cleaned_data.get('subject_name')
        
        # Crée ou récupère l'objet Subject à la validation
        if subject_name:
            subject_obj, _ = Subject.objects.get_or_create(name=subject_name.strip())
            cleaned_data['subject'] = subject_obj
            self.cleaned_data['subject'] = subject_obj
            self.instance.subject = subject_obj
            
        return cleaned_data


ProgramSubjectFormSet = inlineformset_factory(
    Program,
    ProgramSubject,
    form=ProgramSubjectForm,
    extra=0,  # Passer extra=0 en modification évite d'ajouter une ligne vide inutile
    can_delete=True,
    min_num=1,
    validate_min=True
)

class SubjectForm(forms.ModelForm):
    """Création / modification d'une matière."""

    class Meta:
        model = Subject
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex : Mathématiques',
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Généré automatiquement si vide',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['code'].required = False

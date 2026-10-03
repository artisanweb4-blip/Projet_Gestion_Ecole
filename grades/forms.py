from django import forms

from .models import Evaluation, Grade


class EvaluationForm(forms.ModelForm):
    """Création / modification d'une évaluation (devoir, composition...)."""

    class Meta:
        model = Evaluation
        fields = ['title', 'eval_type', 'classroom', 'subject', 'period',
                  'coefficient', 'max_score', 'date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control',
                                            'placeholder': 'Ex : Devoir n°1'}),
            'eval_type': forms.Select(attrs={'class': 'form-control'}),
            'classroom': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'period': forms.Select(attrs={'class': 'form-control'}),
            'coefficient': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'max_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class ExcelImportForm(forms.Form):
    """Formulaire pour l'upload du fichier Excel."""
    evaluation = forms.ModelChoiceField(
        queryset=Evaluation.objects.select_related('classroom', 'subject', 'period'),
        label="Évaluation concernée",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    excel_file = forms.FileField(
        label="Fichier Excel (.xlsx)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx, .xls'})
    )

    def clean_excel_file(self):
        file = self.cleaned_data.get('excel_file')
        if file:
            if not file.name.endswith(('.xlsx', '.xls')):
                raise forms.ValidationError(
                    "Le fichier doit être au format Excel (.xlsx ou .xls)."
                )
        return file


class GradeForm(forms.ModelForm):
    """Formulaire individuel pour saisir ou modifier une note."""
    class Meta:
        model = Grade
        fields = ['score', 'appreciation']
        widgets = {
            'score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25', 'min': '0'}),
            'appreciation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Appréciation...'}),
        }

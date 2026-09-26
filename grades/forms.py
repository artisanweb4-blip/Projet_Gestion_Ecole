from django import forms
from .models import Evaluation, Grade


class ExcelImportForm(forms.Form):
    """Formulaire pour l'upload du fichier Excel"""
    evaluation = forms.ModelChoiceField(
        queryset=Evaluation.objects.all(),
        label="Évaluation concernée",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    excel_file = forms.FileField(
        label="Fichier Excel (.xlsx, .xls)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx, .xls'})
    )

    def clean_excel_file(self):
        file = self.cleaned_data.get('excel_file')
        if file:
            if not file.name.endswith(('.xlsx', '.xls')):
                raise forms.ValidationError("Le fichier doit être au format Excel (.xlsx ou .xls).")
        return file


class GradeForm(forms.ModelForm):
    """Formulaire individuel pour saisir ou modifier une note"""
    class Meta:
        model = Grade
        fields = ['score', 'appreciation']
        widgets = {
            'score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25', 'min': '0'}),
            'appreciation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Appréciation...'}),
        }
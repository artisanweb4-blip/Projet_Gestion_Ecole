from django import forms

from .models import Evaluation, Grade, Period


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


class PeriodForm(forms.ModelForm):
    """Création d'une période de notation (trimestre, semestre…)."""

    class Meta:
        model = Period
        fields = ['name', 'period_type', 'academic_year', 'start_date', 'end_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control',
                                           'placeholder': 'Ex : Trimestre 1'}),
            'period_type': forms.Select(attrs={'class': 'form-control'}),
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control',
                                                 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control',
                                               'type': 'date'}),
        }
        labels = {
            'name': 'Nom de la période',
            'period_type': 'Type',
            'academic_year': 'Année académique',
            'start_date': 'Début',
            'end_date': 'Fin',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_date'].required = False
        self.fields['end_date'].required = False
        self.fields['academic_year'].empty_label = None

    def clean(self):
        cleaned = super().clean()
        year = cleaned.get('academic_year')
        name = (cleaned.get('name') or '').strip()
        if year and name:
            qs = Period._base_manager.filter(
                academic_year=year, name__iexact=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    f"La période « {name} » existe déjà pour l'année {year.name}."
                )
        start, end = cleaned.get('start_date'), cleaned.get('end_date')
        if start and end and end < start:
            raise forms.ValidationError(
                "La date de fin doit être après la date de début."
            )
        return cleaned

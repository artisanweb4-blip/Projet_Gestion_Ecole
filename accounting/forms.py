"""Formulaires du module Comptabilité."""
from django import forms
from django.db.models import Sum

from classes.models import Class
from finance.models import Expense, FeeStructure, StudentPayment, TuitionFee

from students.models import Student

PERIODICITY_PLACEHOLDERS = {
    'MOIS': 'Ex : Octobre 2026',
    'TRIMESTRE': 'Ex : Trimestre 1',
    'SEMESTRE': 'Ex : Semestre 1',
    'ANNUEL': 'Ex : Année 2026-2027',
}


class TuitionFeeForm(forms.ModelForm):
    """Grille des frais de scolarité : par niveau et par périodicité."""

    class Meta:
        model = TuitionFee
        fields = ['level', 'periodicity', 'amount', 'academic_year', 'is_active']
        widgets = {
            'level': forms.Select(attrs={'class': 'form-control'}),
            'periodicity': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '500', 'min': '0',
                'placeholder': 'Ex : 75000',
            }),
            'academic_year': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Ex : 2026-2027',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ExpenseForm(forms.ModelForm):
    """Dépense classée par catégorie."""

    class Meta:
        model = Expense
        fields = ['category', 'label', 'amount', 'expense_date', 'description']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'label': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex : Achat de tables-bancs (Salle 302)',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '500', 'min': '0',
                'placeholder': 'Ex : 150000',
            }),
            'expense_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class PaymentModeForm(forms.Form):
    """Enregistrement d'un paiement : par élève OU par classe entière.

    Le montant attendu est suggéré à partir de la grille des frais
    (niveau de la classe × périodicité).
    """
    MODE_CHOICES = [
        ('ELEVE', 'Un élève'),
        ('CLASSE', 'Toute la classe'),
    ]

    mode = forms.ChoiceField(choices=MODE_CHOICES, initial='ELEVE',
                             widget=forms.RadioSelect(attrs={'class': 'form-check-input'}))
    classroom = forms.ModelChoiceField(
        queryset=Class.objects.none(), required=False,
        empty_label="— Choisir la classe —",
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    student = forms.ModelChoiceField(
        queryset=Student.objects.none(), required=False,
        empty_label="— Choisir l'élève —",
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    periodicity = forms.ChoiceField(
        choices=TuitionFee._meta.get_field('periodicity').choices,
        initial='ANNUEL',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    period_label = forms.CharField(
        required=False, max_length=60,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Ex : Année 2026-2027',
        }),
    )
    amount_paid = forms.DecimalField(
        min_value=0, decimal_places=2, max_digits=12,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 'step': '500', 'min': '0',
            'placeholder': 'Ex : 75000',
        }),
    )
    payment_method = forms.ChoiceField(
        choices=StudentPayment._meta.get_field('payment_method').choices,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        students = (Student.objects.filter(is_active=True)
                    .select_related('class_group')
                    .order_by('class_group__name', 'last_name', 'first_name'))
        self.fields['student'].queryset = students
        self.fields['classroom'].queryset = Class.objects.filter(is_active=True).order_by('name')
        self.fields['student'].widget.optgroups = True  # indicatif, rendu géré au template

    def clean(self):
        cleaned = super().clean()
        mode = cleaned.get('mode')
        if mode == 'ELEVE' and not cleaned.get('student'):
            self.add_error('student', "Choisissez l'élève concerné.")
        if mode == 'CLASSE' and not cleaned.get('classroom'):
            self.add_error('classroom', 'Choisissez la classe concernée.')
        if cleaned.get('mode') == 'ELEVE' and cleaned.get('student'):
            cleaned['classroom'] = cleaned['student'].class_group
        return cleaned


class FeeForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ['name', 'classroom', 'amount', 'due_date', 'academic_year']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['classroom'].required = True
        self.fields['classroom'].empty_label = "— Choisir la classe —"
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex : Scolarité — 1ère tranche',
            }),
            'classroom': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '500', 'min': '0',
                'placeholder': 'Ex : 75000',
            }),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'academic_year': forms.TextInput(attrs={'class': 'form-control'}),
        }
        for name, widget in widgets.items():
            self.fields[name].widget = widget


class PaymentForm(forms.ModelForm):
    """(Conservé pour compatibilité) — le nouveau parcours utilise PaymentModeForm."""

    class Meta:
        model = StudentPayment
        fields = ['student', 'fee_structure', 'amount_paid', 'payment_method',
                  'receipt_number']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fee_structure'].required = False
        self.fields['fee_structure'].empty_label = "— Aucun frais rattaché —"
        self.fields['receipt_number'].required = False
        self.fields['student'].queryset = (
            self.fields['student'].queryset.order_by('last_name', 'first_name')
        )

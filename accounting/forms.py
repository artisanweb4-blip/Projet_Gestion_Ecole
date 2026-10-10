"""Formulaires du module Comptabilité."""
from django import forms

from classes.models import Class
from finance.models import Expense, StudentPayment, TuitionFee

from students.models import Student


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
    """Encaissement : on choisit D'ABORD la classe, puis l'élève de cette
    classe (ou toute la classe). Montant suggéré par la grille des frais
    (niveau × périodicité) ; reçu A5 généré pour chaque élève.
    """
    MODE_CHOICES = [
        ('ELEVE', 'Un élève de la classe'),
        ('CLASSE', 'Toute la classe'),
    ]

    classroom = forms.ModelChoiceField(
        queryset=Class.objects.none(), required=True,
        empty_label="— Choisir la classe —",
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    mode = forms.ChoiceField(choices=MODE_CHOICES, initial='ELEVE',
                             widget=forms.RadioSelect(attrs={'class': 'form-check-input'}))
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
        self.fields['classroom'].queryset = (
            Class.objects.filter(is_active=True).order_by('name'))
        self.fields['student'].queryset = (
            Student.objects.filter(is_active=True)
            .select_related('class_group')
            .order_by('last_name', 'first_name'))

    def clean(self):
        cleaned = super().clean()
        classroom = cleaned.get('classroom')
        student = cleaned.get('student')
        mode = cleaned.get('mode')
        if classroom and student and student.class_group_id != classroom.pk:
            self.add_error(
                'student',
                "L'élève choisi n'appartient pas à la classe sélectionnée.")
        if mode == 'ELEVE' and not student:
            self.add_error('student',
                           "Choisissez l'élève dans la classe sélectionnée.")
        return cleaned

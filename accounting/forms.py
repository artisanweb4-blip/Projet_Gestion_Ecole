from django import forms

from finance.models import FeeStructure, StudentPayment


class FeeForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ['name', 'classroom', 'amount', 'due_date', 'academic_year']
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


class PaymentForm(forms.ModelForm):
    class Meta:
        model = StudentPayment
        fields = ['student', 'fee_structure', 'amount_paid', 'payment_method',
                  'receipt_number']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'fee_structure': forms.Select(attrs={'class': 'form-control'}),
            'amount_paid': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '500', 'min': '0',
                'placeholder': 'Ex : 75000',
            }),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'receipt_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Généré automatiquement si vide',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fee_structure'].required = False
        self.fields['fee_structure'].empty_label = "— Aucun frais rattaché —"
        self.fields['receipt_number'].required = False
        self.fields['student'].queryset = (
            self.fields['student'].queryset.order_by('last_name', 'first_name')
        )

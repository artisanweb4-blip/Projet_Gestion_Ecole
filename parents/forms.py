from django import forms

from .models import Parent


class ParentForm(forms.ModelForm):
    class Meta:
        model = Parent
        fields = ['civility', 'first_name', 'last_name', 'email', 'phone',
                  'profession', 'address']
        widgets = {
            'civility': forms.Select(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control',
                                                 'placeholder': 'Prénom'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control',
                                                'placeholder': 'Nom de famille'}),
            'email': forms.EmailInput(attrs={'class': 'form-control',
                                             'placeholder': 'email@exemple.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control',
                                            'placeholder': '+223 00 00 00 00'}),
            'profession': forms.TextInput(attrs={'class': 'form-control',
                                                 'placeholder': 'Ex : Commerçant'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

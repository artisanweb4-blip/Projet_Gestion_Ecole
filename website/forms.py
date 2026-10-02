"""
Formulaires publics (inscription d'une école) et plateforme (super admin).
"""
from django import forms

from accounts.models import School, User


class _SchoolAdminFieldsMixin(forms.Form):
    """Champs du compte administrateur de l'école."""
    admin_first_name = forms.CharField(
        label="Prénom de l'administrateur", max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Ex : Awa'}),
    )
    admin_last_name = forms.CharField(
        label="Nom de l'administrateur", max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Ex : DIALLO'}),
    )
    admin_email = forms.EmailField(
        label="Email administrateur",
        widget=forms.EmailInput(attrs={'placeholder': 'direction@mon-ecole.ml'}),
    )
    admin_password = forms.CharField(
        label="Mot de passe", widget=forms.PasswordInput(attrs={'placeholder': '••••••••'}),
        help_text="Au moins 6 caractères.",
    )

    def clean_admin_email(self):
        email = self.cleaned_data['admin_email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Un compte utilise déjà cet email.")
        return email

    def clean_admin_password(self):
        pwd = self.cleaned_data['admin_password']
        if len(pwd) < 6:
            raise forms.ValidationError("Le mot de passe doit contenir au moins 6 caractères.")
        return pwd


class SchoolRegistrationForm(_SchoolAdminFieldsMixin, forms.ModelForm):
    """Inscription publique : crée l'école + son compte administrateur."""

    class Meta:
        model = School
        fields = ['name', 'address', 'phone', 'email']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': "Ex : Groupe Scolaire La Réussite"}),
            'address': forms.TextInput(attrs={'placeholder': 'Ville, quartier...'}),
            'phone': forms.TextInput(attrs={'placeholder': '+223 00 00 00 00'}),
            'email': forms.EmailInput(attrs={'placeholder': 'contact@mon-ecole.ml'}),
        }

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if School.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError("Une école porte déjà ce nom.")
        return name


class PlatformSchoolForm(_SchoolAdminFieldsMixin, forms.ModelForm):
    """Création d'une école par le super admin (plateforme)."""

    class Meta:
        model = School
        fields = ['name', 'plan', 'address', 'phone', 'email']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': "Nom de l'école"}),
            'plan': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'placeholder': 'Adresse'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Téléphone'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
        }

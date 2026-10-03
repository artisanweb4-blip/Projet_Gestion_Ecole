"""
Formulaires publics (inscription d'une école) et plateforme (super admin).
"""
from django import forms

from accounts.models import PlatformSetting, School, SubscriptionPlan, User


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

    subscription = forms.ModelChoiceField(
        label="Abonnement", required=False, empty_label="— Aucun —",
        queryset=SubscriptionPlan.objects.filter(is_active=True),
    )
    subscription_until = forms.DateField(
        label="Valable jusqu'au", required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

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


class PlatformSchoolUpdateForm(forms.ModelForm):
    """Modification d'une école existante par le super admin."""

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

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        exists = School.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists()
        if exists:
            raise forms.ValidationError("Une école porte déjà ce nom.")
        return name


class PlatformUserForm(forms.ModelForm):
    """Création d'un compte utilisateur (par le super admin)."""

    password = forms.CharField(
        label="Mot de passe", widget=forms.PasswordInput(attrs={'placeholder': '••••••••'}),
        help_text="Au moins 6 caractères.",
    )

    gender = forms.ChoiceField(
        label="Sexe", required=False,
        choices=[('', '— Non renseigné —')] + list(User.GENDER_CHOICES),
    )
    region = forms.ChoiceField(
        label="Région", required=False,
        choices=[('', '— Non renseignée —')] + list(User.REGION_CHOICES),
    )

    class Meta:
        model = User
        fields = ['school', 'role', 'first_name', 'last_name', 'email',
                  'gender', 'region']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Prénom'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Nom'}),
            'email': forms.EmailInput(attrs={'placeholder': 'utilisateur@ecole.ml'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['school'].queryset = School.objects.order_by('name')
        self.fields['school'].empty_label = "— Aucune école (plateforme) —"

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Un compte utilise déjà cet email.")
        return email

    def clean_password(self):
        pwd = self.cleaned_data['password']
        if len(pwd) < 6:
            raise forms.ValidationError("Le mot de passe doit contenir au moins 6 caractères.")
        return pwd


class PlatformUserPasswordForm(forms.Form):
    """Réinitialisation du mot de passe d'un compte."""

    password = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••'}),
    )
    password_confirm = forms.CharField(
        label="Confirmation",
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••'}),
    )

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get('password') or ''
        if len(pwd) < 6:
            raise forms.ValidationError("Le mot de passe doit contenir au moins 6 caractères.")
        if pwd != cleaned.get('password_confirm'):
            raise forms.ValidationError("Les deux mots de passe ne correspondent pas.")
        return cleaned


class PlatformSchoolSubscriptionForm(forms.ModelForm):
    """Attribution / modification de l'abonnement d'une école."""

    class Meta:
        model = School
        fields = ['subscription', 'subscription_until']
        widgets = {
            'subscription_until': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subscription'].queryset = SubscriptionPlan.objects.order_by('price')
        self.fields['subscription'].empty_label = "— Aucun —"


class PlatformSubscriptionForm(forms.ModelForm):
    """Création / modification d'une formule d'abonnement."""

    class Meta:
        model = SubscriptionPlan
        fields = ['name', 'price', 'duration_days', 'max_students',
                  'description', 'features', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'features': forms.Textarea(attrs={'rows': 4}),
        }


class PlatformSettingsForm(forms.ModelForm):
    """Paramètres généraux de la plateforme."""

    class Meta:
        model = PlatformSetting
        fields = ['platform_name', 'support_email',
                  'public_registration_enabled', 'default_plan']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['default_plan'].queryset = SubscriptionPlan.objects.order_by('price')
        self.fields['default_plan'].empty_label = "— Aucun —"

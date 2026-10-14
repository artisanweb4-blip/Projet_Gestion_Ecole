from django import forms
from .models import GeneralSetting, SchoolSetting, NotificationSetting, BackupSetting


class GeneralSettingForm(forms.ModelForm):
    class Meta:
        model = GeneralSetting
        fields = [
            'country_name',
            'motto',
            'ministry',
            'directorate',
            'director_name',
            'current_academic_year',
            'is_bilingual',
        ]
        widgets = {
            'country_name': forms.TextInput(attrs={'class': 'form-control'}),
            'motto': forms.TextInput(attrs={'class': 'form-control'}),
            'ministry': forms.TextInput(attrs={'class': 'form-control'}),
            'directorate': forms.TextInput(attrs={'class': 'form-control'}),
            'director_name': forms.TextInput(attrs={'class': 'form-control'}),
            'current_academic_year': forms.TextInput(attrs={'class': 'form-control'}),
            'is_bilingual': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SchoolSettingForm(forms.ModelForm):
    class Meta:
        model = SchoolSetting
        fields = ['logo', 'school_name', 'address', 'phone', 'email']
        widgets = {
            'school_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class NotificationSettingForm(forms.ModelForm):
    class Meta:
        model = NotificationSetting
        fields = ['email_notifications', 'sms_notifications']


class BackupSettingForm(forms.ModelForm):
    class Meta:
        model = BackupSetting
        fields = ['auto_backup']


class UserCreateForm(forms.ModelForm):
    """Création d'un utilisateur de l'école (Paramètres → Utilisateurs).

    - Le nom d'utilisateur est généré automatiquement depuis l'email ;
    - Le mot de passe est chiffré (set_password), jamais stocké en clair ;
    - L'utilisateur est rattaché à l'école de l'administrateur connecté.
    """

    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=6,
        help_text='6 caractères minimum',
    )

    class Meta:
        from django.contrib.auth import get_user_model
        model = get_user_model()
        fields = ['first_name', 'last_name', 'email', 'phone', 'role']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'Prénom',
            'last_name': 'Nom de famille',
            'email': 'Adresse email (identifiant de connexion)',
            'phone': 'Téléphone',
            'role': "Rôle dans l'établissement",
        }

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()

    def save(self, commit=True, school=None):
        User = self._meta.model
        user = super().save(commit=False)
        email = self.cleaned_data['email']
        base = email.split('@')[0].replace('+', '')[:145] or 'user'
        username, i = base, 1
        while User._base_manager.filter(username=username).exists():
            username = f'{base}{i}'
            i += 1
        user.username = username
        user.email = email
        if school is not None:
            user.school = school
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

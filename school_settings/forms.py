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
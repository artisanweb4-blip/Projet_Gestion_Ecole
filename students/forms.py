from django import forms
from .models import Student

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'photo', 'gender', 'date_of_birth',
            'place_of_birth', 'nationality', 'religion', 'address', 'phone',
            'email', 'blood_group', 'allergies', 'medical_notes',
            'emergency_contact_name', 'emergency_contact_phone',
            'class_group', 'parents', 'is_active', 'documents'
        ]
        widgets = {
            'parents': forms.SelectMultiple(attrs={'size': 1,
                'title': 'Liste déroulante — maintenez Ctrl pour choisir plusieurs parents'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'},
                                             format='%Y-%m-%d'),
            'address': forms.Textarea(attrs={'rows': 3}),
            'medical_notes': forms.Textarea(attrs={'rows': 2}),
        }
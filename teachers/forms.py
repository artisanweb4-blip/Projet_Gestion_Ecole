from django import forms
from .models import Teacher

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            'first_name', 
            'last_name', 
            'email', 
            'phone', 
            'specialization', 
            'hire_date', 
            'photo'
        ]
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Injection automatique de la classe CSS form-control sur tous les champs
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})



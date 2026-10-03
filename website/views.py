"""
Pages publiques : landing page et inscription d'une école.
"""
from django import forms
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from accounts.models import School, User
from classes.models import Class
from students.models import Student
from teachers.models import Teacher

from .forms import SchoolRegistrationForm


def landing(request):
    """Page d'accueil publique de la plateforme."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    # Une installation mono-école existante doit aussi être comptée :
    # la table School ne recense que les établissements inscrits en ligne.
    nb_schools = School.objects.filter(is_active=True).count()
    if nb_schools == 0:
        from school_settings.models import SchoolSetting
        nb_schools = 1 if SchoolSetting.objects.exists() else 0

    context = {
        'nb_schools': nb_schools,
        'nb_students': Student.objects.filter(is_active=True).count(),
        'nb_teachers': Teacher.objects.filter(is_active=True).count(),
        'nb_classes': Class.objects.count(),
    }
    return render(request, 'website/landing.html', context)


@require_http_methods(['GET', 'POST'])
def register_school(request):
    """Inscription publique d'une école : école + compte administrateur."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = SchoolRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        school = form.save(commit=False)
        school.email = school.email or form.cleaned_data['admin_email']
        school.save()

        admin = User.objects.create_user(
            email=form.cleaned_data['admin_email'],
            username=form.cleaned_data['admin_email'].split('@')[0],
            password=form.cleaned_data['admin_password'],
            first_name=form.cleaned_data['admin_first_name'],
            last_name=form.cleaned_data['admin_last_name'],
            role='ADMIN',
        )
        admin.school = school
        admin.is_staff = True
        admin.save()

        # Paramètres de l'établissement dédiés à cette nouvelle école
        from school_settings.models import SchoolSetting
        SchoolSetting.objects.get_or_create(
            school=school,
            defaults={
                'school_name': school.name,
                'address': school.address, 'phone': school.phone,
                'email': school.email,
            },
        )

        auth_login(request, admin)
        messages.success(
            request,
            f"Bienvenue ! L'école « {school.name} » a été créée. "
            "Votre compte administrateur est prêt."
        )
        return redirect('dashboard')

    return render(request, 'website/register_school.html', {'form': form})

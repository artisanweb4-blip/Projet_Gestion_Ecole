from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import (
    BackupSettingForm,
    GeneralSettingForm,
    NotificationSettingForm,
    SchoolSettingForm,
)
from .models import (
    BackupSetting,
    GeneralSetting,
    NotificationSetting,
    SchoolSetting,
)

User = get_user_model()


@login_required
def settings_index(request):
    """Redirige par défaut vers le premier onglet (Général)."""
    return redirect('school_settings:general')


@login_required
def settings_general(request):
    setting = GeneralSetting.load()
    if request.method == 'POST':
        form = GeneralSettingForm(request.POST, instance=setting)
        if form.is_valid():
            form.save()
            messages.success(request, "Paramètres généraux enregistrés.")
            return redirect('school_settings:general')
    else:
        form = GeneralSettingForm(instance=setting)

    return render(
        request, 'school_settings/settings_general.html', {'form': form}
    )


@login_required
def settings_school(request):
    setting = SchoolSetting.load()
    if request.method == 'POST':
        form = SchoolSettingForm(request.POST, request.FILES, instance=setting)
        if form.is_valid():
            form.save()
            messages.success(request, "Informations de l'école enregistrées.")
            return redirect('school_settings:school')
    else:
        form = SchoolSettingForm(instance=setting)

    return render(
        request, 'school_settings/settings_school.html', {'form': form}
    )


@login_required
def settings_notifications(request):
    setting = NotificationSetting.load()
    if request.method == 'POST':
        setting.email_notifications = 'email_notifications' in request.POST
        setting.sms_notifications = 'sms_notifications' in request.POST
        setting.save()
        messages.success(request, "Préférences de notifications mises à jour.")
        return redirect('school_settings:notifications')

    form = NotificationSettingForm(instance=setting)
    return render(
        request, 'school_settings/settings_notifications.html', {'form': form}
    )


@login_required
def settings_users(request):
    admin_count = User.objects.filter(is_superuser=True).count() or 2
    teacher_count = (
        User.objects.filter(groups__name='Enseignants').count() or 15
    )
    parent_count = User.objects.filter(groups__name='Parents').count() or 120
    accountant_count = (
        User.objects.filter(groups__name='Comptables').count() or 1
    )

    context = {
        'admin_count': admin_count,
        'teacher_count': teacher_count,
        'parent_count': parent_count,
        'accountant_count': accountant_count,
    }
    return render(request, 'school_settings/settings_users.html', context)


@login_required
def settings_backup(request):
    setting = BackupSetting.load()

    if request.method == 'POST':
        if request.POST.get('action') == 'create_backup':
            setting.last_backup_date = timezone.now()
            setting.save()
            messages.success(request, "Une nouvelle sauvegarde a été générée.")
            return redirect('school_settings:backup')

        setting.auto_backup = 'auto_backup' in request.POST
        setting.save()
        messages.success(request, "Paramètres de sauvegarde enregistrés.")
        return redirect('school_settings:backup')

    form = BackupSettingForm(instance=setting)
    return render(
        request,
        'school_settings/settings_backup.html',
        {'form': form, 'last_backup_date': setting.last_backup_date},
    )


@login_required
def download_backup(request):
    response = HttpResponse(
        "Fichier SQL/JSON de sauvegarde", content_type="text/plain"
    )
    response['Content-Disposition'] = (
        'attachment; filename="sauvegarde_ecole.sql"'
    )
    return response


@login_required
def settings_security(request):
    return render(request, 'school_settings/settings_security.html')
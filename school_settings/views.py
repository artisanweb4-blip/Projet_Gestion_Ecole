from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.html import format_html

from .excel_backup import build_xlsx, collect_school_data
from .forms import (
    BackupSettingForm,
    GeneralSettingForm,
    NotificationSettingForm,
    SchoolSettingForm,
    UserCreateForm,
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


def _can_manage_users(user):
    """Seuls la direction et le superadmin gèrent les utilisateurs."""
    return user.is_superuser or getattr(user, 'role', '') == 'ADMIN'


@login_required
def settings_users(request):
    """Onglet Utilisateurs : liste réelle de l'école + création."""
    school = getattr(request.user, 'school', None)
    users = User.objects.filter(school=school).order_by('role', 'last_name') if school else User.objects.none()

    counts = {
        'admin_count': users.filter(role='ADMIN').count(),
        'teacher_count': users.filter(role='TEACHER').count(),
        'parent_count': users.filter(role='PARENT').count(),
        'accountant_count': users.filter(role='COMPTABLE').count(),
    }

    can_manage = _can_manage_users(request.user)
    form = UserCreateForm()
    if request.method == 'POST' and request.POST.get('add_user'):
        if not can_manage:
            messages.error(request, "Seule la direction peut créer des utilisateurs.")
            return redirect('school_settings:users')
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save(school=school)
            messages.success(
                request,
                "Utilisateur {} créé. Identifiant de connexion : {}".format(
                    user.get_full_name() or user.email, user.email
                ),
            )
            return redirect('school_settings:users')

    context = dict(counts)
    context.update({
        'users_list': users,
        'form': form,
        'can_manage': can_manage,
    })
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
    """Télécharge TOUTES les données de l'école dans un classeur Excel."""
    school = getattr(request.user, 'school', None)
    if school is None:
        messages.error(
            request, "Aucune école rattachée à votre compte : sauvegarde impossible."
        )
        return redirect('school_settings:backup')

    sheets = collect_school_data(school)
    content = build_xlsx(sheets)

    setting = BackupSetting.load()
    setting.last_backup_date = timezone.now()
    setting.save()

    stamp = timezone.localtime().strftime('%Y-%m-%d_%Hh%M')
    code = (school.code or 'ecole').replace('/', '-')
    response = HttpResponse(
        content,
        content_type=(
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ),
    )
    response['Content-Disposition'] = (
        f'attachment; filename="sauvegarde_{code}_{stamp}.xlsx"'
    )
    return response


@login_required
def settings_security(request):
    return render(request, 'school_settings/settings_security.html')
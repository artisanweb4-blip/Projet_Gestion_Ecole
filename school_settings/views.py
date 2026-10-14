from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.html import format_html

from .excel_backup import build_xlsx, collect_school_data
from .importer import IMPORT_SPECS, run_import
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
        {'form': form, 'last_backup_date': setting.last_backup_date,
         'import_specs': IMPORT_SPECS},
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
def import_template(request, category):
    """Modèle Excel à remplir (en-têtes + ligne d'exemple).

    Pour « tout » : télécharge la sauvegarde complète actuelle — c'est le
    fichier à utiliser pour l'import de toutes les données en une fois.
    """
    spec = IMPORT_SPECS.get(category)
    if spec is None:
        return redirect('school_settings:backup')

    if category == 'tout':
        school = getattr(request.user, 'school', None)
        if school is None:
            messages.error(request, "Aucune école rattachée à votre compte.")
            return redirect('school_settings:backup')
        content = build_xlsx(collect_school_data(school))
        response = HttpResponse(
            content,
            content_type=(
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ),
        )
        response['Content-Disposition'] = (
            'attachment; filename="import_complet_ecole.xlsx"'
        )
        return response

    content = build_xlsx([(spec['label'], spec['headers'], [spec['example']])])
    response = HttpResponse(
        content,
        content_type=(
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ),
    )
    response['Content-Disposition'] = (
        f'attachment; filename="modele_import_{category}.xlsx"'
    )
    return response


@login_required
def import_data(request):
    """Importe des données Excel dans le système (Élèves, Enseignants…)."""
    school = getattr(request.user, 'school', None)
    if school is None:
        messages.error(request, "Aucune école rattachée à votre compte.")
        return redirect('school_settings:backup')
    if not (request.user.is_superuser or getattr(request.user, 'role', '') == 'ADMIN'):
        messages.error(request, "Seule la direction peut importer des données.")
        return redirect('school_settings:backup')

    if request.method != 'POST':
        return redirect('school_settings:backup')

    category = request.POST.get('category', '')
    if category not in IMPORT_SPECS:
        messages.error(request, "Type de données inconnu.")
        return redirect('school_settings:backup')

    upload = request.FILES.get('file')
    if upload is None:
        messages.error(request, "Choisissez un fichier Excel (.xlsx) à importer.")
        return redirect('school_settings:backup')
    if not upload.name.lower().endswith('.xlsx'):
        messages.error(
            request, "Format non supporté : enregistrez le fichier au format .xlsx."
        )
        return redirect('school_settings:backup')

    result = run_import(school, category, upload.read())
    label = IMPORT_SPECS[category]['label']
    if result['total'] and result.get('per_category'):
        detail = ' ; '.join(
            f"{cat} : {c} créé(s), {u} mis à jour"
            for cat, c, u in result['per_category']
        )
        messages.success(request, f"Import complet — {detail}.")
    elif result['total']:
        messages.success(
            request,
            f"Import {label} : {result['created']} créé(s), {result['updated']} mis à jour."
        )
    if result['errors']:
        for err in result['errors'][:8]:
            messages.warning(request, err)
        if len(result['errors']) > 8:
            messages.warning(request, f"… et {len(result['errors']) - 8} autre(s) erreur(s).")
    if not result['total'] and not result['errors']:
        messages.warning(request, "Aucune donnée à importer (feuille vide).")
    return redirect('school_settings:backup')


@login_required
def settings_security(request):



    return render(request, 'school_settings/settings_security.html')
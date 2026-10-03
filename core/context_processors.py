"""
Processeurs de contexte globaux : menu latéral, informations de l'école.
"""
from datetime import date

from django.urls import reverse

MENU = [
    {'section': 'Pilotage'},
    {'label': 'Tableau de bord', 'url_name': 'dashboard', 'icon': 'fa-gauge-high', 'prefix': '/dashboard'},
    {'section': 'Plateforme — Super Admin'},
    {'label': 'Tableau de bord', 'url_name': 'platform_dashboard',
     'icon': 'fa-gauge-high', 'prefix': '/platform', 'superuser_only': True},
    {'label': 'Écoles', 'url_name': 'platform_schools',
     'icon': 'fa-school', 'prefix': '/platform/schools', 'superuser_only': True},
    {'label': 'Abonnements', 'url_name': 'platform_subscriptions',
     'icon': 'fa-credit-card', 'prefix': '/platform/subscriptions', 'superuser_only': True},
    {'label': 'Utilisateurs', 'url_name': 'platform_users',
     'icon': 'fa-users-gear', 'prefix': '/platform/users', 'superuser_only': True},
    {'label': 'Analytique', 'url_name': 'platform_analytics',
     'icon': 'fa-chart-pie', 'prefix': '/platform/analytics', 'superuser_only': True},
    {'label': 'Paramètres', 'url_name': 'platform_settings',
     'icon': 'fa-sliders', 'prefix': '/platform/settings', 'superuser_only': True},
    {'section': 'Scolarité'},
    {'label': 'Élèves', 'url_name': 'students:list', 'icon': 'fa-user-graduate', 'prefix': '/students'},
    {'label': 'Enseignants', 'url_name': 'teachers:list', 'icon': 'fa-chalkboard-user', 'prefix': '/teachers'},
    {'label': 'Parents', 'url_name': 'parents:list', 'icon': 'fa-users', 'prefix': '/parents'},
    {'label': 'Classes', 'url_name': 'classes:list', 'icon': 'fa-school', 'prefix': '/classes'},
    {'label': 'Matières & Programmes', 'url_name': 'courses:program_list', 'icon': 'fa-book-open', 'prefix': '/courses'},
    {'section': 'Évaluations'},
    {'label': 'Notes', 'url_name': 'grades:grade_list', 'icon': 'fa-pen-to-square', 'prefix': '/grades/'},
    {'label': 'Saisie des notes', 'url_name': 'grades:grade_entry', 'icon': 'fa-table-list', 'prefix': '/grades/entry'},
    {'label': 'Bulletins', 'url_name': 'grades:bulletin_select', 'icon': 'fa-file-lines', 'prefix': '/grades/bulletins'},
    {'section': 'Finances'},
    {'label': 'Comptabilité', 'url_name': 'accounting:index', 'icon': 'fa-coins', 'prefix': '/accounting',
     'roles': ['ADMIN', 'COMPTABLE']},
    {'label': 'Frais scolaires', 'url_name': 'accounting:fees', 'icon': 'fa-file-invoice-dollar', 'prefix': '/accounting',
     'roles': ['ADMIN', 'COMPTABLE']},
    {'label': 'Paiements', 'url_name': 'accounting:payments', 'icon': 'fa-money-bill-wave', 'prefix': '/accounting',
     'roles': ['ADMIN', 'COMPTABLE']},
    {'section': 'Organisation'},
    {'label': 'Emploi du temps', 'url_name': 'timetable:index', 'icon': 'fa-calendar-days', 'prefix': '/timetable'},
    {'label': 'Calendrier scolaire', 'url_name': 'school_calendar:calendar', 'icon': 'fa-calendar-check', 'prefix': '/calendar'},
    {'section': 'Administration'},
    {'label': 'Documents', 'url_name': 'documents:index', 'icon': 'fa-folder-open', 'prefix': '/documents'},
    {'label': 'Paramètres', 'url_name': 'school_settings:index', 'icon': 'fa-gear', 'prefix': '/settings'},
]


def build_menu(request):
    """Construit la liste des entrées de menu avec URL résolue + état actif.

    Les entrées déclarant une clé `roles` ne sont visibles que pour ces rôles
    (les superutilisateurs voient tout).
    """
    user = request.user
    is_superuser = getattr(user, 'is_superuser', False)
    user_role = str(getattr(user, 'role', '') or '').upper()

    items = []
    for entry in MENU:
        if 'section' in entry:
            items.append({'section': entry['section'], 'is_section': True})
            continue

        allowed_roles = entry.get('roles')
        if allowed_roles and not is_superuser and user_role not in allowed_roles:
            continue
        if entry.get('superuser_only') and not is_superuser:
            continue

        try:
            url = reverse(entry['url_name'])
        except Exception:
            url = '#'
        path = request.path
        is_active = path == url or (
            entry['prefix'] != '/dashboard' and path.startswith(entry['prefix'])
        )
        item = dict(entry)
        item['url'] = url
        item['is_active'] = is_active
        item['is_section'] = False
        items.append(item)
    return items


def global_context(request):
    """Injecte le menu, l'école et l'année courante dans tous les templates."""
    school = None
    try:
        from school_settings.models import SchoolSetting
        school = SchoolSetting.load()
    except Exception:
        school = None

    menu = build_menu(request)
    # Titre + icône de la page courante : préfixe le plus long correspondant
    active_page_label = None
    active_page_icon = 'fa-gauge-high'
    best_len = -1
    path = request.path
    for item in menu:
        if item.get('is_section'):
            continue
        if path == item.get('url'):
            active_page_label, active_page_icon = item['label'], item.get('icon', active_page_icon)
            best_len = 10_000
            break
        prefix = item.get('prefix', '')
        if prefix != '/dashboard' and path.startswith(prefix) and len(prefix) > best_len:
            best_len = len(prefix)
            active_page_label = item['label']
            active_page_icon = item.get('icon', active_page_icon)

    return {
        'menu_items': menu,
        'active_page_label': active_page_label,
        'active_page_icon': active_page_icon,
        'school': school,
        'current_year': date.today().year,
    }

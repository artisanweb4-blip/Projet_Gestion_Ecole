"""
Processeurs de contexte globaux : menu latéral, informations de l'école.
"""
from django.urls import reverse

MENU = [
    {'section': 'Pilotage'},
    {'label': 'Tableau de bord', 'url_name': 'dashboard', 'icon': 'fa-gauge-high', 'prefix': '/dashboard'},
    {'section': 'Scolarité'},
    {'label': 'Élèves', 'url_name': 'students:list', 'icon': 'fa-user-graduate', 'prefix': '/students'},
    {'label': 'Enseignants', 'url_name': 'teachers:list', 'icon': 'fa-chalkboard-user', 'prefix': '/teachers'},
    {'label': 'Parents', 'url_name': 'parents:list', 'icon': 'fa-users', 'prefix': '/parents'},
    {'label': 'Classes', 'url_name': 'classes:list', 'icon': 'fa-school', 'prefix': '/classes'},
    {'label': 'Matières & Programmes', 'url_name': 'courses:program_list', 'icon': 'fa-book-open', 'prefix': '/courses'},
    {'section': 'Évaluations'},
    {'label': 'Notes', 'url_name': 'grades:grade_list', 'icon': 'fa-pen-to-square', 'prefix': '/grades/entry'},
    {'label': 'Saisie des notes', 'url_name': 'grades:grade_entry', 'icon': 'fa-table-list', 'prefix': '/grades/entry'},
    {'label': 'Bulletins', 'url_name': 'grades:bulletin_select', 'icon': 'fa-file-lines', 'prefix': '/grades/bulletins'},
    {'section': 'Organisation'},
    {'label': 'Emploi du temps', 'url_name': 'timetable:index', 'icon': 'fa-calendar-days', 'prefix': '/timetable'},
    {'label': 'Calendrier scolaire', 'url_name': 'school_calendar:calendar', 'icon': 'fa-calendar-check', 'prefix': '/calendar'},
    {'section': 'Administration'},
    {'label': 'Documents', 'url_name': 'documents:index', 'icon': 'fa-folder-open', 'prefix': '/documents'},
    {'label': 'Paramètres', 'url_name': 'school_settings:index', 'icon': 'fa-gear', 'prefix': '/settings'},
]


def build_menu(request):
    """Construit la liste des entrées de menu avec URL résolue + état actif."""
    items = []
    for entry in MENU:
        if 'section' in entry:
            items.append({'section': entry['section'], 'is_section': True})
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

    return {
        'menu_items': build_menu(request),
        'school': school,
        'current_year': __import__('datetime').date.today().year,
    }

"""Sauvegarde de toutes les données de l'école au format Excel (.xlsx).

Générateur XLSX « maison » (zip + XML) : AUCUNE dépendance externe —
fonctionne sur une machine hors ligne sans pip install.
Un classeur = une feuille par catégorie de données, filtrées par école.
"""
import io
import zipfile
from datetime import date, datetime, time
from decimal import Decimal
from xml.sax.saxutils import escape

CT_NS = 'http://schemas.openxmlformats.org/package/2006/content-types'
R_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
REL_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
MAIN_NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'


def _col_letter(index):
    """0 -> A, 1 -> B, ..., 26 -> AA"""
    s = ''
    index += 1
    while index:
        index, rest = divmod(index - 1, 26)
        s = chr(65 + rest) + s
    return s


def _cell(ref, value):
    if value is None or value == '':
        return f'<c r="{ref}"/>'
    if isinstance(value, bool):
        return f'<c r="{ref}" t="b"><v>{1 if value else 0}</v></c>'
    if isinstance(value, (int, float)):
        return f'<c r="{ref}"><v>{value}</v></c>'
    if isinstance(value, Decimal):
        return f'<c r="{ref}"><v>{value}</v></c>'
    if isinstance(value, datetime):
        value = value.strftime('%d/%m/%Y %H:%M')
    elif isinstance(value, date):
        value = value.strftime('%d/%m/%Y')
    elif isinstance(value, time):
        value = value.strftime('%H:%M')
    text = escape(str(value))
    return (
        f'<c r="{ref}" t="inlineStr">'
        f'<is><t xml:space="preserve">{text}</t></is></c>'
    )


def _sheet_xml(headers, rows):
    cols = ''.join(
        f'<col min="{i + 1}" max="{i + 1}" width="{max(12, min(38, len(str(h)) + 4))}" customWidth="1"/>'
        for i, h in enumerate(headers)
    )
    header_row = ''.join(
        f'<c r="{_col_letter(i)}1" t="inlineStr" s="1">'
        f'<is><t xml:space="preserve">{escape(str(h))}</t></is></c>'
        for i, h in enumerate(headers)
    )
    body = []
    for r, row in enumerate(rows, start=2):
        cells = ''.join(_cell(f'{_col_letter(i)}{r}', v) for i, v in enumerate(row))
        body.append(f'<row r="{r}">{cells}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<worksheet xmlns="{MAIN_NS}">{cols}<sheetData>'
        f'<row r="1">{header_row}</row>{"".join(body)}'
        '</sheetData></worksheet>'
    )


def build_xlsx(sheets):
    """sheets : liste de (nom, en-têtes, lignes) -> bytes d'un classeur .xlsx"""
    # Noms de feuilles : 31 caractères max, caractères interdits supprimés
    clean = []
    seen = set()
    for name, headers, rows in sheets:
        name = ''.join(c for c in str(name) if c not in '[]:*?/\\')[:31] or 'Feuille'
        base, n = name, 2
        while name in seen:
            name = f'{base[:28]} ({n})'
            n += 1
        seen.add(name)
        clean.append((name, headers or ['Vide'], rows or []))

    workbook_sheets = ''.join(
        f'<sheet name="{escape(n)}" sheetId="{i + 1}" r:id="rId{i + 1}"/>'
        for i, (n, _, _) in enumerate(clean)
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<workbook xmlns="{MAIN_NS}" xmlns:r="{R_NS}">'
        f'<sheets>{workbook_sheets}</sheets></workbook>'
    )
    wb_rels = ''.join(
        f'<Relationship Id="rId{i + 1}" Type="{R_NS}/worksheet" '
        f'Target="worksheets/sheet{i + 1}.xml"/>'
        for i in range(len(clean))
    )
    wb_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{REL_NS}">{wb_rels}'
        f'<Relationship Id="rId{len(clean) + 1}" Type="{R_NS}/styles" Target="styles.xml"/>'
        '</Relationships>'
    )
    content_types = ''.join(
        f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" '
        f'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for i in range(len(clean))
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Types xmlns="{CT_NS}">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        f'{content_types}'
        '<Override PartName="/xl/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        '</Types>'
    )
    styles = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<styleSheet xmlns="{MAIN_NS}">'
        '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
        '<font><b/><sz val="11"/><color rgb="FF065F46"/><name val="Calibri"/></font></fonts>'
        '<fills count="2"><fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill></fills>'
        '<borders count="1"><border/></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="2">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
        '</cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        '</styleSheet>'
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{REL_NS}">'
        f'<Relationship Id="rId1" Type="{R_NS}/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )

    parts = {
        '[Content_Types].xml': content_types,
        '_rels/.rels': root_rels,
        'xl/workbook.xml': workbook,
        'xl/_rels/workbook.xml.rels': wb_rels,
        'xl/styles.xml': styles,
    }
    for i, (_, headers, rows) in enumerate(clean):
        parts[f'xl/worksheets/sheet{i + 1}.xml'] = _sheet_xml(headers, rows)

    # Filet de sécurité : tout fragment doit être du XML bien formé
    from xml.etree import ElementTree
    for name, xml_text in parts.items():
        ElementTree.fromstring(xml_text.encode('UTF-8'))

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, xml_text in parts.items():
            z.writestr(name, xml_text)
    return buf.getvalue()


# =============================================================================
# COLLECTE DES DONNÉES DE L'ÉCOLE (feuilles du classeur)
# =============================================================================

def _person(obj):
    return f'{obj.last_name} {obj.first_name}'.strip()


def _day_label(obj):
    return obj.get_day_of_week_display()


def collect_school_data(school):
    """Construit toutes les feuilles pour une école donnée.

    La première feuille « École » reprend les informations saisies dans
    Paramètres → École (nom, adresse, téléphone, email) et → Général
    (ministère / direction de tutelle, pays, devise, année scolaire).
    """
    from accounts.models import User
    from classes.models import Class
    from courses.models import Program, ProgramSubject, Subject
    from finance.models import Expense, StudentPayment, TuitionFee
    from grades.models import Grade
    from parents.models import Parent
    from school_settings.models import GeneralSetting, SchoolSetting
    from students.models import Student
    from teachers.models import Teacher
    from timetable.models import Classroom, TimeSlot
    from django.utils import timezone as dj_tz

    general = GeneralSetting.load()
    setting = SchoolSetting.load(school)
    _pick = lambda a, b: a if a else b  # valeur onglet École d'abord

    sheets = []

    sheets.append(('École',
                   ['Information', 'Valeur'],
                   [
                       ["Nom de l'école", _pick(setting.school_name, school.name)],
                       ['Adresse', _pick(setting.address, school.address) or ''],
                       ['Téléphone', _pick(setting.phone, school.phone) or ''],
                       ['Email', _pick(setting.email, school.email) or ''],
                       ["Code école", school.code or ''],
                       ['Ministère de tutelle', general.ministry or ''],
                       ['Direction de tutelle', general.directorate or ''],
                       ['Nom du directeur', general.director_name or ''],
                       ['Pays', general.country_name or ''],
                       ['Devise', general.motto or ''],
                       ['Année scolaire', general.current_academic_year or ''],
                       ['Sauvegarde générée le',
                        dj_tz.localtime().strftime('%d/%m/%Y %H:%M')],
                   ]))

    users = User.objects.filter(school=school).order_by('role', 'last_name')
    sheets.append(('Utilisateurs',
                   ['Prénom', 'Nom', 'Email', "Nom d'utilisateur", 'Rôle',
                    'Téléphone', 'Actif', 'Créé le'],
                   [[u.first_name, u.last_name, u.email, u.username,
                     u.get_role_display(), u.phone, u.is_active, u.created_at]
                    for u in users]))

    students = Student.objects.filter(school=school).order_by('class_group__name', 'last_name')
    sheets.append(('Élèves',
                   ['Matricule', 'Prénom', 'Nom', 'Sexe', 'Date de naissance',
                    'Lieu de naissance', 'Classe', 'Téléphone', 'Email',
                    'Date inscription', 'Actif'],
                   [[s.student_id, s.first_name, s.last_name, s.get_gender_display(),
                     s.date_of_birth, s.place_of_birth,
                     s.class_group.name if s.class_group else '',
                     s.phone, s.email, s.enrollment_date, s.is_active]
                    for s in students]))

    teachers = Teacher.objects.filter(school=school).order_by('last_name')
    sheets.append(('Enseignants',
                   ['Matricule', 'Nom', 'Prénom', 'Spécialité', 'Embauché le',
                    'Téléphone', 'Email', 'Actif'],
                   [[t.employee_id, t.last_name, t.first_name, t.specialization,
                     t.hire_date, t.phone, t.email, t.is_active]
                    for t in teachers]))

    parents = Parent.objects.filter(school=school).order_by('last_name')
    sheets.append(('Parents',
                   ['Civilité', 'Nom', 'Prénom', 'Email', 'Téléphone',
                    'Profession', 'Adresse'],
                   [[p.get_civility_display(), p.last_name, p.first_name,
                     p.email, p.phone, p.profession, p.address]
                    for p in parents]))

    classes = Class.objects.filter(school=school).order_by('name')
    sheets.append(('Classes',
                   ['Classe', 'Programme', 'Niveau', 'Section', 'Capacité', 'Active'],
                   [[c.name, c.program.name if c.program else '', c.get_level_display()
                     if hasattr(c, 'get_level_display') else c.level,
                     c.section, c.capacity, c.is_active]
                    for c in classes]))

    rooms = Classroom.objects.filter(school=school).order_by('name')
    sheets.append(('Salles', ['Salle', 'Capacité', 'Bâtiment'],
                   [[r.name, r.capacity, r.building] for r in rooms]))

    subjects = Subject.objects.filter(school=school).order_by('name')
    sheets.append(('Matières', ['Matière', 'Code', 'Active'],
                   [[s.name, s.code, s.is_active] for s in subjects]))

    programs = Program.objects.filter(school=school).order_by('name')
    sheets.append(('Programmes', ['Code', 'Programme', 'Description'],
                   [[p.code, p.name, p.description] for p in programs]))

    links = ProgramSubject.objects.filter(program__school=school).order_by('program__name')
    sheets.append(('Programmes - Matières',
                   ['Programme', 'Matière', 'Enseignant', 'Coefficient',
                    'Heures/semaine', 'Heures total', 'Optionnelle'],
                   [[l.program.name, l.subject.name, _person(l.teacher) if l.teacher else '',
                     l.coefficient, l.hours_per_week, l.total_hours, l.is_optional]
                    for l in links]))

    slots = TimeSlot.objects.filter(school_class__school=school).order_by(
        'school_class__name', 'day_of_week', 'start_time')
    sheets.append(('Emploi du temps',
                   ['Classe', 'Jour', 'Début', 'Fin', 'Matière', 'Enseignant', 'Salle'],
                   [[s.school_class.name, _day_label(s), s.start_time, s.end_time,
                     s.subject.name, _person(s.teacher) if s.teacher else '',
                     s.classroom.name if s.classroom else '']
                    for s in slots]))

    payments = StudentPayment.objects.filter(school=school).order_by('-payment_date')
    sheets.append(('Paiements',
                   ['Reçu', 'Élève', 'Classe', 'Périodicité', 'Période',
                    'Montant', 'Date', 'Mode', 'Reçu émis'],
                   [[p.receipt_number,
                     _person(p.student) if p.student else '',
                     p.student.class_group.name if p.student and p.student.class_group else '',
                     p.get_periodicity_display(), p.period_label,
                     p.amount_paid, p.payment_date,
                     p.get_payment_method_display(), p.is_receipt_issued]
                    for p in payments]))

    fees = TuitionFee.objects.filter(school=school).order_by('level')
    sheets.append(('Frais par niveau',
                   ['Niveau', 'Périodicité', 'Montant', 'Année académique', 'Actif'],
                   [[f.get_level_display() if hasattr(f, 'get_level_display') else f.level,
                     f.get_periodicity_display(),
                     f.amount, f.academic_year, f.is_active] for f in fees]))

    expenses = Expense.objects.filter(school=school).order_by('-expense_date')
    sheets.append(('Dépenses',
                   ['Catégorie', 'Libellé', 'Montant', 'Date', 'Description'],
                   [[e.get_category_display(), e.label, e.amount,
                     e.expense_date, e.description] for e in expenses]))

    grades = Grade.objects.filter(student__school=school).order_by('-updated_at')
    sheets.append(('Notes',
                   ['Élève', 'Évaluation', 'Note', 'Appréciation'],
                   [[_person(g.student) if g.student else '',
                     str(g.evaluation), g.score, g.appreciation] for g in grades]))

    return sheets


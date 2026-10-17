"""Import de données Excel (.xlsx) dans le système — SANS dépendance externe.

Fonctionne main dans la main avec la sauvegarde Excel : le fichier exporté
peut être complété puis ré-importé tel quel (le lecteur retrouve la bonne
feuille par son nom). Chaque catégorie est créée OU mise à jour (upsert)
par sa clé naturelle — pas de doublons.
"""
import io
import re
import zipfile
from datetime import date, datetime, timedelta
from xml.etree import ElementTree as ET

NS_MAIN = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
REL_MAIN = '{http://schemas.openxmlformats.org/package/2006/relationships}'
OD_REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'


# =============================================================================
# LECTEUR XLSX minimal (feuilles -> en-têtes + lignes de texte)
# =============================================================================

def _col_index(ref):
    """'BC12' -> index 0-based de la colonne."""
    letters = re.match(r'([A-Z]+)', ref or '')
    if not letters:
        return None
    n = 0
    for ch in letters.group(1):
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _cell_value(cell, shared):
    t = cell.get('t')
    if t == 'inlineStr':
        node = cell.find(f'{NS_MAIN}is')
        if node is None:
            return ''
        return ''.join(x.text or '' for x in node.iter(f'{NS_MAIN}t')).strip()
    v = cell.find(f'{NS_MAIN}v')
    if v is None or v.text is None:
        return ''
    if t == 's':
        try:
            return shared[int(v.text)].strip()
        except (ValueError, IndexError):
            return ''
    return v.text.strip()


def read_xlsx(data):
    """bytes d'un .xlsx -> {nom_feuille: (en_tetes, lignes)}.

    Chaque ligne est une liste de chaînes (ou nombres en texte), alignée
    sur les en-têtes (cases vides = '').
    """
    zf = zipfile.ZipFile(io.BytesIO(data))

    shared = []
    if 'xl/sharedStrings.xml' in zf.namelist():
        root = ET.fromstring(zf.read('xl/sharedStrings.xml'))
        for si in root.findall(f'{NS_MAIN}si'):
            shared.append(''.join(x.text or '' for x in si.iter(f'{NS_MAIN}t')))

    wb = ET.fromstring(zf.read('xl/workbook.xml'))
    rels = ET.fromstring(zf.read('xl/_rels/workbook.xml.rels'))
    rel_map = {
        rel.get('Id'): rel.get('Target')
        for rel in rels.findall(f'{REL_MAIN}Relationship')
    }

    sheets = {}
    for sheet in wb.iter(f'{NS_MAIN}sheet'):
        name = sheet.get('name')
        rid = sheet.get(f'{OD_REL}id')
        target = rel_map.get(rid, '')
        target = target.lstrip('/')
        if not target.startswith('xl/'):
            target = 'xl/' + target
        if target not in zf.namelist():
            continue
        root = ET.fromstring(zf.read(target))
        grid = {}
        max_col = 0
        for row in root.iter(f'{NS_MAIN}row'):
            r_num = int(row.get('r', len(grid) + 1))
            cells = {}
            for cell in row.findall(f'{NS_MAIN}c'):
                idx = _col_index(cell.get('r'))
                if idx is None:
                    idx = max(cells) + 1 if cells else 0
                cells[idx] = _cell_value(cell, shared)
                max_col = max(max_col, idx + 1)
            grid[r_num] = cells

        rows_sorted = [grid[k] for k in sorted(grid)]
        if not rows_sorted:
            sheets[name] = ([], [])
            continue

        header_cells = rows_sorted[0]
        n_cols = max(max_col, (max(header_cells) + 1) if header_cells else 0)
        headers = [(header_cells.get(i) or '').strip() for i in range(n_cols)]
        body = []
        for cells in rows_sorted[1:]:
            line = [(cells.get(i) or '').strip() for i in range(n_cols)]
            if any(line):
                body.append(line)
        sheets[name] = (headers, body)
    return sheets


def pick_sheet(sheets, wanted):
    """Retrouve la feuille voulue (nom exact, sans accents, ou 1re feuille)."""
    if wanted in sheets:
        return sheets[wanted]
    def norm(s):
        return re.sub(r'[^a-z]', '', s.lower())
    target = norm(wanted)
    for name, content in sheets.items():
        if norm(name) == target:
            return content
    for name, content in sheets.items():
        if target and target in norm(name):
            return content
    if sheets:
        return next(iter(sheets.values()))
    return ([], [])


# =============================================================================
# CONVERTISSEURS
# =============================================================================

def parse_date(value):
    """'26/09/2010', '2010-09-26' ou numéro série Excel -> date | None | 'INVALID'."""
    s = str(value or '').strip()
    if not s:
        return None
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%y'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    try:
        n = float(s)
        if 20000 < n < 80000:
            return date(1899, 12, 30) + timedelta(days=int(n))
    except ValueError:
        pass
    return 'INVALID'


def parse_bool(value, default=True):
    s = str(value or '').strip().lower()
    if s in ('', 'none'):
        return default
    return s in ('oui', 'true', '1', 'vrai', 'yes', 'x', 'actif')


def parse_int(value, default=None):
    s = str(value or '').strip().replace(' ', '')
    if not s:
        return default
    try:
        return int(float(s))
    except ValueError:
        return default


def norm_gender(value):
    s = str(value or '').strip().lower()
    if s in ('m', 'masculin', 'garçon', 'garcon'):
        return 'M'
    if s in ('f', 'féminin', 'feminin', 'fille'):
        return 'F'
    return ''


def norm_civility(value):
    s = str(value or '').strip().lower()
    if s in ('mme', 'madame', 'mme.', 'f'):
        return 'Mme'
    return 'M'


def match_choice(value, choices):
    """Retrouve le code d'un choix par code OU par libellé (sans accents)."""
    s = str(value or '').strip()
    if not s:
        return ''
    for code, label in choices:
        if s == code or s == label:
            return code
    def norm(x):
        return re.sub(r'[^a-z0-9]', '', x.lower())
    t = norm(s)
    for code, label in choices:
        if norm(code) == t or norm(label) == t:
            return code
    return ''


class RowError(Exception):
    pass


# =============================================================================
# SPÉCIFICATIONS D'IMPORT PAR CATÉGORIE
# =============================================================================

def _upsert_student(school, row):
    from students.models import Student
    required = {'Prénom': row.get('Prénom'), 'Nom': row.get('Nom')}
    if not all(required.values()):
        raise RowError('Prénom et Nom obligatoires')
    dob = parse_date(row.get('Date de naissance'))
    if dob == 'INVALID':
        raise RowError('Date de naissance invalide (attendu JJ/MM/AAAA)')

    matricule = str(row.get('Matricule') or '').strip()
    obj = None
    if matricule:
        obj = Student._base_manager.filter(school=school, student_id=matricule).first()
    obj = obj or Student(school=school)
    if obj.pk is None and matricule:
        # respecte le matricule fourni à la création (round-trip sauvegarde)
        obj.student_id = matricule[:20]

    obj.first_name = row['Prénom'].strip()
    obj.last_name = row['Nom'].strip()
    obj.gender = norm_gender(row.get('Sexe'))
    obj.date_of_birth = dob
    obj.place_of_birth = row.get('Lieu de naissance') or ''
    obj.phone = row.get('Téléphone') or ''
    obj.email = row.get('Email') or ''
    obj.is_active = parse_bool(row.get('Actif'), True)
    enrol = parse_date(row.get('Date inscription'))
    if enrol == 'INVALID':
        raise RowError("Date d'inscription invalide (attendu JJ/MM/AAAA)")
    obj.enrollment_date = enrol or date.today()

    class_name = str(row.get('Classe') or '').strip()
    if class_name:
        from classes.models import Class
        klass = Class.objects.filter(school=school, name__iexact=class_name).first()
        if klass is None:
            # crée la classe manquante pour ne pas bloquer l'import
            klass = Class.objects.create(school=school, name=class_name)
        obj.class_group = klass
    created = obj.pk is None
    obj.save()
    return created, obj


def _upsert_teacher(school, row):
    from teachers.models import Teacher
    if not (row.get('Nom') or row.get('Prénom')):
        raise RowError('Nom ou Prénom obligatoire')
    matricule = str(row.get('Matricule') or '').strip()
    obj = None
    if matricule:
        obj = Teacher._base_manager.filter(school=school, employee_id=matricule).first()
    if obj is None and row.get('Email'):
        obj = Teacher._base_manager.filter(school=school, email=row['Email'].strip()).first()
    obj = obj or Teacher(school=school)
    if obj.pk is None and matricule:
        # respecte le matricule fourni à la création (round-trip sauvegarde)
        obj.employee_id = matricule[:20]

    obj.last_name = (row.get('Nom') or '').strip()
    obj.first_name = (row.get('Prénom') or '').strip()
    obj.specialization = row.get('Spécialité') or ''
    hire = parse_date(row.get('Embauché le'))
    if hire == 'INVALID':
        raise RowError("Date d'embauche invalide (attendu JJ/MM/AAAA)")
    obj.hire_date = hire or date.today()
    obj.phone = row.get('Téléphone') or ''
    obj.email = row.get('Email') or ''
    obj.is_active = parse_bool(row.get('Actif'), True)
    created = obj.pk is None
    obj.save()
    return created, obj


def _upsert_parent(school, row):
    from parents.models import Parent
    if not (row.get('Nom') or row.get('Prénom')):
        raise RowError('Nom ou Prénom obligatoire')
    email = (row.get('Email') or '').strip().lower()
    obj = None
    if email:
        obj = Parent._base_manager.filter(school=school, email=email).first()
    if obj is None:
        q = Parent._base_manager.filter(school=school,
                                        last_name=(row.get('Nom') or '').strip())
        if row.get('Téléphone'):
            q = q.filter(phone=row['Téléphone'].strip())
        obj = q.first()
    obj = obj or Parent(school=school)

    obj.civility = norm_civility(row.get('Civilité'))
    obj.last_name = (row.get('Nom') or '').strip()
    obj.first_name = (row.get('Prénom') or '').strip()
    obj.email = email or None
    obj.phone = row.get('Téléphone') or ''
    obj.profession = row.get('Profession') or ''
    obj.address = row.get('Adresse') or ''
    created = obj.pk is None
    obj.save()
    return created, obj


def _upsert_class(school, row):
    from classes.models import Class
    name = (row.get('Classe') or '').strip()
    if not name:
        raise RowError('Nom de classe obligatoire')
    obj = Class.objects.filter(school=school, name__iexact=name).first()
    obj = obj or Class(school=school, name=name)

    prog_name = (row.get('Programme') or '').strip()
    if prog_name:
        from courses.models import Program
        prog = Program.objects.filter(school=school, name__iexact=prog_name).first()
        if prog is None:
            prog = Program.objects.create(school=school, name=prog_name)
        obj.program = prog
    level = match_choice(row.get('Niveau'), Class._meta.get_field('level').choices)
    obj.level = level or (row.get('Niveau') or '')[:20]
    obj.section = (row.get('Section') or 'Française').strip() or 'Française'
    obj.capacity = parse_int(row.get('Capacité'))
    obj.is_active = parse_bool(row.get('Active'), True)
    created = obj.pk is None
    obj.save()
    return created, obj


def _upsert_subject(school, row):
    from courses.models import Subject
    name = (row.get('Matière') or '').strip()
    if not name:
        raise RowError('Nom de matière obligatoire')
    obj = Subject.objects.filter(school=school, name__iexact=name).first()
    obj = obj or Subject(school=school, name=name)
    obj.code = (row.get('Code') or '').strip() or None
    obj.is_active = parse_bool(row.get('Active'), True)
    created = obj.pk is None
    obj.save()
    return created, obj


def _upsert_classroom(school, row):
    from timetable.models import Classroom
    name = (row.get('Salle') or '').strip()
    if not name:
        raise RowError('Nom de salle obligatoire')
    obj = Classroom.objects.filter(school=school, name__iexact=name).first()
    obj = obj or Classroom(school=school, name=name)
    obj.capacity = parse_int(row.get('Capacité'))
    obj.building = (row.get('Bâtiment') or row.get('Batiment') or '').strip()
    created = obj.pk is None
    obj.save()
    return created, obj


IMPORT_SPECS = {
    'tout': {
        'label': 'Toutes les données (fichier de sauvegarde complet)',
    },
    'eleves': {
        'label': 'Élèves',
        'sheet': 'Élèves',
        'headers': ['Matricule', 'Prénom', 'Nom', 'Sexe', 'Date de naissance',
                    'Lieu de naissance', 'Classe', 'Téléphone', 'Email',
                    'Date inscription', 'Actif'],
        'example': ['EXEMPLE-001', 'Awa', 'TRAORE', 'F', '26/09/2010', 'Bamako',
                    'L1', '76 00 00 00', 'awa@ex.ml', '15/09/2026', 'Oui'],
        'upsert': _upsert_student,
    },
    'enseignants': {
        'label': 'Enseignants',
        'sheet': 'Enseignants',
        'headers': ['Matricule', 'Nom', 'Prénom', 'Spécialité', 'Embauché le',
                    'Téléphone', 'Email', 'Actif'],
        'example': ['EXEMPLE-ENS', 'DIALLO', 'Aminata', 'Informatique',
                    '01/09/2024', '76 11 11 11', 'diallo@ex.ml', 'Oui'],
        'upsert': _upsert_teacher,
    },
    'parents': {
        'label': 'Parents',
        'sheet': 'Parents',
        'headers': ['Civilité', 'Nom', 'Prénom', 'Email', 'Téléphone',
                    'Profession', 'Adresse'],
        'example': ['M.', 'TRAORE', 'Moussa', 'moussa@ex.ml', '76 22 22 22',
                    'Commerçant', 'Bamako'],
        'upsert': _upsert_parent,
    },
    'classes': {
        'label': 'Classes',
        'sheet': 'Classes',
        'headers': ['Classe', 'Programme', 'Niveau', 'Section', 'Capacité', 'Active'],
        'example': ['L1', 'Licence 1', 'L1', 'Française', '30', 'Oui'],
        'upsert': _upsert_class,
    },
    'matieres': {
        'label': 'Matières',
        'sheet': 'Matières',
        'headers': ['Matière', 'Code', 'Active'],
        'example': ['Algorithmique', 'ALGO-1', 'Oui'],
        'upsert': _upsert_subject,
    },
    'salles': {
        'label': 'Salles',
        'sheet': 'Salles',
        'headers': ['Salle', 'Capacité', 'Bâtiment'],
        'example': ['L1 Informatique', '30', 'Bâtiment Principal'],
        'upsert': _upsert_classroom,
    },
}


def _norm_header(h):
    return re.sub(r'\s+', ' ', h or '').strip().lower()


def _match_headers(spec, headers):
    """Positions des colonnes attendues d'après la ligne d'en-tête."""
    idx = {}
    for pos, h in enumerate(headers):
        h_clean = _norm_header(h)
        for expected in spec['headers']:
            if h_clean == _norm_header(expected):
                idx[expected] = pos
                break
    return idx


def _find_sheet_exact(sheets, wanted):
    """Retrouve la feuille par nom exact ou sans accents — SANS repli sur
    la 1re feuille (sécurité pour l'import complet)."""
    if wanted in sheets:
        return sheets[wanted]
    def norm(s):
        return re.sub(r'[^a-z]', '', s.lower())
    t = norm(wanted)
    for name, content in sheets.items():
        if norm(name) == t:
            return content
    return ([], [])


def _import_sheet(school, spec, headers, rows):
    """Importe les lignes d'une feuille reconnue.

    Retourne (created, updated, errors) ou None si colonnes non reconnues.
    """
    idx = _match_headers(spec, headers)
    required_min = len(spec['headers']) - 2
    if len(idx) < required_min:
        return None

    created = updated = 0
    errors = []
    for n, line in enumerate(rows, start=2):
        row = {h: (line[idx[h]] if h in idx and idx[h] < len(line) else '')
               for h in spec['headers']}
        key_vals = [v for h, v in row.items() if h not in ('Matricule', 'Actif', 'Code', 'Active')]
        if not any(str(v or '').strip() for v in key_vals):
            continue
        first = next(iter(row.values()))
        if str(first or '').upper().startswith('EXEMPLE'):
            continue  # ligne d'exemple du modèle
        try:
            was_created, _obj = spec['upsert'](school, row)
            if was_created:
                created += 1
            else:
                updated += 1
        except RowError as e:
            errors.append(f'Ligne {n} : {e}')
        except Exception as e:  # pragma: no cover — robustesse
            errors.append(f'Ligne {n} : erreur ({e})')
        if len(errors) >= 15:
            errors.append('… import interrompu (trop d’erreurs).')
            break
    return created, updated, errors


def run_import(school, category, data):
    """Importe un .xlsx. Retourne un dict de rapport.

    - catégorie simple : une seule feuille (repli intelligent sur le nom) ;
    - « tout » : parcourt TOUTES les catégories du fichier de sauvegarde
      complet en une seule opération et cumule les rapports par catégorie.
    """
    spec = IMPORT_SPECS[category]
    sheets = read_xlsx(data)

    if category == 'tout':
        total_created = total_updated = 0
        per_category = []
        all_errors = []
        for key, sp in IMPORT_SPECS.items():
            if key == 'tout' or 'headers' not in sp:
                continue
            headers, rows = _find_sheet_exact(sheets, sp['sheet'])
            if not headers:
                continue
            res = _import_sheet(school, sp, headers, rows)
            if res is None:
                continue
            created, updated, errors = res
            per_category.append((sp['label'], created, updated))
            all_errors.extend(f"{sp['label']} — {e}" for e in errors)
            total_created += created
            total_updated += updated
        return {
            'created': total_created, 'updated': total_updated,
            'errors': all_errors, 'total': total_created + total_updated,
            'per_category': per_category,
        }

    headers, rows = pick_sheet(sheets, spec['sheet'])
    if not headers:
        return {'created': 0, 'updated': 0, 'errors': ['Feuille vide ou illisible.'],
                'total': 0}

    res = _import_sheet(school, spec, headers, rows)
    if res is None:
        return {'created': 0, 'updated': 0,
                'errors': [f"Colonnes non reconnues. Utilisez le modèle : {', '.join(spec['headers'])}."],
                'total': 0}
    created, updated, errors = res
    return {'created': created, 'updated': updated, 'errors': errors,
            'total': created + updated}

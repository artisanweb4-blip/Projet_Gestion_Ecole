"""
Logique métier des moyennes, coefficients et rangs (module Notes & Bulletins).

Règles de calcul :
- Chaque note est ramenée sur 20 : note20 = score / barème × 20.
- La moyenne d'une matière est la moyenne des notes ramenées sur 20,
  pondérées par le coefficient de chaque évaluation.
- Le coefficient d'une matière vient du programme de la classe
  (courses.ProgramSubject) ; à défaut, il vaut 1.
- La moyenne générale = Σ(moyenne_matière × coefficient_matière) / Σ(coefficients).
- Le rang se calcule par classe, avec gestion des ex æquo
  (classement « compétition » : 1, 2, 2, 4...).
"""
from collections import OrderedDict

from courses.models import ProgramSubject


def get_class_coefficients(classroom):
    """Retourne {subject_id: coefficient} depuis le programme de la classe."""
    coefficients = {}
    if classroom is not None and getattr(classroom, 'program', None):
        for ps in classroom.program.program_subjects.select_related('subject'):
            coefficients[ps.subject_id] = float(ps.coefficient)
    return coefficients


def subject_breakdown(student, period, coefficients=None, prefetched_grades=None):
    """
    Agrège les notes d'un élève pour une période, matière par matière.

    prefetched_grades permet de passer des notes déjà chargées en base
    (optimisation : évite une requête par élève dans le calcul de rangs).

    Retourne une liste de dicts triée par nom de matière :
    {subject, average, coefficient, points, appreciation, details: [...]}
    """
    if prefetched_grades is None:
        prefetched_grades = (
            Grade.objects.filter(
                student=student,
                evaluation__period=period,
                score__isnull=False,
            )
            .select_related('evaluation', 'evaluation__subject')
            .order_by('evaluation__date', 'evaluation__id')
        )
    grades = prefetched_grades

    if coefficients is None:
        coefficients = get_class_coefficients(getattr(student, 'class_group', None))

    subjects = OrderedDict()
    for grade in grades:
        evaluation = grade.evaluation
        entry = subjects.setdefault(evaluation.subject_id, {
            'subject': evaluation.subject,
            'total_weighted': 0.0,
            'total_coef': 0.0,
            'details': [],
        })
        max_score = float(evaluation.max_score or 20)
        note20 = (float(grade.score) / max_score) * 20.0
        eval_coef = float(evaluation.coefficient or 1)
        entry['total_weighted'] += note20 * eval_coef
        entry['total_coef'] += eval_coef
        entry['details'].append({
            'grade': grade,
            'evaluation': evaluation,
            'note20': round(note20, 2),
            'eval_coef': evaluation.coefficient,
        })

    rows = []
    for entry in subjects.values():
        average = (
            round(entry['total_weighted'] / entry['total_coef'], 2)
            if entry['total_coef'] else None
        )
        coefficient = coefficients.get(entry['subject'].id, 1.0) or 1.0
        rows.append({
            'subject': entry['subject'],
            'average': average,
            'coefficient': coefficient,
            'points': round(average * coefficient, 2) if average is not None else None,
            'appreciation': appreciation_for(average),
            'details': entry['details'],
        })

    rows.sort(key=lambda r: r['subject'].name.lower())
    return rows


def general_average(rows):
    """Moyenne générale pondérée à partir des lignes de subject_breakdown."""
    total_points = sum(r['points'] for r in rows if r['points'] is not None)
    total_coef = sum(r['coefficient'] for r in rows if r['points'] is not None)
    if total_coef == 0:
        return None
    return round(total_points / total_coef, 2)


def class_ranking(classroom, period):
    """
    Calcule les moyennes générales de tous les élèves d'une classe.

    Retourne (résultats, rangs, moyenne_de_classe) :
    - résultats : liste [{student, average, rank}] (inclut les élèves sans note, rank=None)
    - rangs : {student_id: rang}
    - moyenne_de_classe : moyenne des moyennes générales
    """
    from .models import Grade  # import local pour éviter toute circularité

    coefficients = get_class_coefficients(classroom)
    students = list(classroom.students.filter(is_active=True))

    # Toutes les notes de la classe en UNE seule requête
    all_grades = (
        Grade.objects
        .filter(student__in=students, evaluation__period=period,
                score__isnull=False)
        .select_related('evaluation', 'evaluation__subject')
        .order_by('evaluation__date', 'evaluation__id')
    )
    grades_by_student = {}
    for grade in all_grades:
        grades_by_student.setdefault(grade.student_id, []).append(grade)

    results = []
    for student in students:
        rows = subject_breakdown(
            student, period, coefficients,
            prefetched_grades=grades_by_student.get(student.id, []),
        )
        results.append({
            'student': student,
            'average': general_average(rows),
            'rank': None,
        })

    ranked = sorted(
        [r for r in results if r['average'] is not None],
        key=lambda x: x['average'],
        reverse=True,
    )

    ranks = {}
    prev_avg = None
    prev_rank = 0
    for position, item in enumerate(ranked, start=1):
        if item['average'] == prev_avg:
            item['rank'] = prev_rank
        else:
            item['rank'] = position
            prev_rank = position
            prev_avg = item['average']
        ranks[item['student'].id] = item['rank']

    averages = [r['average'] for r in results if r['average'] is not None]
    class_average = (
        round(sum(averages) / len(averages), 2) if averages else None
    )
    return results, ranks, class_average


def mention_for(average):
    """Mention associée à une moyenne générale (sur 20)."""
    if average is None:
        return ''
    if average >= 16:
        return 'Très Bien'
    if average >= 14:
        return 'Bien'
    if average >= 12:
        return 'Assez Bien'
    if average >= 10:
        return 'Passable'
    return 'Insuffisant'


def appreciation_for(average):
    """Appréciation automatique pour une moyenne de matière (sur 20)."""
    if average is None:
        return ''
    if average >= 16:
        return 'Très bon travail'
    if average >= 14:
        return 'Bon travail'
    if average >= 12:
        return 'Travail satisfaisant'
    if average >= 10:
        return 'Travail acceptable'
    if average >= 8:
        return 'Travail insuffisant'
    return 'Travail très insuffisant'


# Import placé en fin de module pour la lisibilité des dépendances
from .models import Grade  # noqa: E402

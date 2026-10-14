"""
Vues du module Notes & Bulletins :
- Liste des évaluations + import Excel
- Saisie des notes par classe / matière (grille)
- Bulletins (moyennes, coefficients, rangs) + exports PDF & Excel
"""
import os
from io import BytesIO

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.urls import reverse
from django_htmx.http import HttpResponseClientRedirect
from xhtml2pdf import pisa

from classes.models import Class
from courses.models import Subject
from school_settings.models import GeneralSetting, SchoolSetting
from students.models import Student

from .forms import PeriodForm, EvaluationForm, ExcelImportForm
from .models import AcademicYear, Evaluation, Grade, Period
from .services import (
    appreciation_for,
    class_ranking,
    general_average,
    mention_for,
    subject_breakdown,
)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _school():
    """Informations de l'établissement (singleton SchoolSetting)."""
    try:
        return SchoolSetting.load()
    except Exception:
        return None


def _bulletin_header_context(school_setting):
    """Contexte d'en-tête des bulletins : infos onglet École (avec repli),
    logo résolu sur disque et tutelles / république (Paramètres → Général)."""
    school = getattr(school_setting, 'school', None)
    logo_path = None
    if school_setting is not None and getattr(school_setting, 'logo', None):
        try:
            if school_setting.logo.storage.exists(school_setting.logo.name):
                logo_path = school_setting.logo.path
        except Exception:
            logo_path = None
    ctx = {
        'school_name': (getattr(school_setting, 'school_name', None)
                        or getattr(school, 'name', None) or "Gestion d'École"),
        'school_address': (getattr(school_setting, 'address', None)
                           or getattr(school, 'address', None)),
        'school_phone': (getattr(school_setting, 'phone', None)
                         or getattr(school, 'phone', None)),
        'school_email': (getattr(school_setting, 'email', None)
                         or getattr(school, 'email', None)),
        'logo_path': logo_path,
        'general': GeneralSetting.load(),
    }
    if school_setting is not None and getattr(school_setting, 'logo', None):
        try:
            ctx['logo_url'] = school_setting.logo.url
        except Exception:
            ctx['logo_url'] = None
    return ctx


def _render_pdf(template_src, context, filename):
    """Génère un PDF à partir d'un template HTML (xhtml2pdf)."""
    html = render_to_string(template_src, context)
    result = BytesIO()

    def _link(uri, rel):
        # Ressources locales (logo de l'école) résolues sur le disque
        return uri if uri and os.path.exists(uri) else None

    pdf = pisa.pisaDocument(
        BytesIO(html.encode('UTF-8')), result, encoding='UTF-8',
        link_callback=_link)
    if pdf.err:
        return HttpResponse(
            "Erreur lors de la génération du PDF.", status=500
        )
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# --------------------------------------------------------------------------
# Évaluations & liste des notes
# --------------------------------------------------------------------------

@login_required
def grade_list(request):
    """Vue principale : liste des évaluations et formulaire d'import Excel."""
    evaluations = Evaluation.objects.select_related(
        'classroom', 'subject', 'period', 'period__academic_year'
    ).all()

    classroom_id = request.GET.get('classroom')
    subject_id = request.GET.get('subject')
    period_id = request.GET.get('period')
    if classroom_id:
        evaluations = evaluations.filter(classroom_id=classroom_id)
    if subject_id:
        evaluations = evaluations.filter(subject_id=subject_id)
    if period_id:
        evaluations = evaluations.filter(period_id=period_id)

    context = {
        'evaluations': evaluations,
        'form': ExcelImportForm(),
        'classrooms': Class.objects.filter(is_active=True),
        'subjects': Subject.objects.all(),
        'periods': Period.objects.select_related('academic_year'),
        'f_classroom': classroom_id or '',
        'f_subject': subject_id or '',
        'f_period': period_id or '',
    }
    return render(request, 'grades/grade_list.html', context)


def _current_academic_year(school):
    """Année académique active de l'école, créée au besoin depuis les
    Paramètres → Général (année scolaire en cours)."""
    from datetime import date as _date
    from school_settings.models import GeneralSetting

    year = AcademicYear.objects.filter(school=school, is_active=True).first()
    if year:
        return year

    today = _date.today()
    default_name = GeneralSetting.load().current_academic_year
    if not default_name:
        default_name = f"{today.year}-{today.year + 1}" if today.month >= 9 \
            else f"{today.year - 1}-{today.year}"
    year, _created = AcademicYear.objects.get_or_create(
        school=school, name=default_name,
        defaults=dict(start_date=_date(today.year, 9, 1),
                      end_date=_date(today.year + 1, 6, 30), is_active=True),
    )
    # une seule année active à la fois
    AcademicYear.objects.filter(school=school).exclude(pk=year.pk) \
        .update(is_active=False)
    year.is_active = True
    year.save()
    return year


@login_required
def period_create(request):
    """Ajout d'une période (trimestre, semestre…) en modale."""
    school = getattr(request.user, 'school', None)
    year = _current_academic_year(school)
    initial = {}
    if year:
        initial['academic_year'] = year

    form = PeriodForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        period = form.save(commit=False)
        period.school = school
        period.save()
        messages.success(request, f"Période « {period.name} » créée.")
        target = (request.POST.get('next') or request.GET.get('next')
                  or reverse('grades:grade_entry'))
        if request.htmx:
            return HttpResponseClientRedirect(target)
        return redirect(target)

    if request.htmx:
        return render(request, 'includes/form_modal.html', {
            'form': form,
            'modal_title': 'Nouvelle période',
            'modal_action': request.get_full_path(),
        })
    return render(request, 'grades/evaluation_form.html', {
        'form': form,
        'title': 'Nouvelle période',
        'next_url': '',
    })


@login_required
def evaluation_create(request):
    """Création d'une évaluation, puis retour à la saisie des notes."""
    next_url = request.GET.get('next') or request.POST.get('next')
    initial = {}
    for param in ('classroom', 'subject', 'period'):
        value = request.GET.get(param)
        if value:
            initial[param] = value
    default_date = request.GET.get('date') or None
    if default_date:
        initial['date'] = default_date

    form = EvaluationForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        evaluation = form.save()
        messages.success(request, f"Évaluation « {evaluation.title} » créée avec succès.")
        target = next_url or reverse('grades:grade_entry_eval', args=[evaluation.pk])
        if request.htmx:
            return HttpResponseClientRedirect(target)
        return redirect(target)

    if request.htmx:
        return render(request, 'includes/form_modal.html', {
            'form': form,
            'modal_title': 'Nouvelle évaluation',
            'modal_action': request.get_full_path(),
        })
    return render(request, 'grades/evaluation_form.html', {
        'form': form,
        'title': 'Nouvelle évaluation',
        'next_url': next_url or '',
    })


@login_required
def evaluation_edit(request, pk):
    evaluation = get_object_or_404(Evaluation, pk=pk)
    form = EvaluationForm(request.POST or None, instance=evaluation)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Évaluation mise à jour.")
        if request.htmx:
            return HttpResponseClientRedirect(reverse('grades:grade_list'))
        return redirect('grades:grade_list')

    if request.htmx:
        return render(request, 'includes/form_modal.html', {
            'form': form,
            'modal_title': f"Modifier : {evaluation.title}",
            'modal_action': request.get_full_path(),
        })
    return render(request, 'grades/evaluation_form.html', {
        'form': form,
        'title': f"Modifier : {evaluation.title}",
        'next_url': '',
    })


@login_required
def evaluation_delete(request, pk):
    evaluation = get_object_or_404(Evaluation, pk=pk)
    if request.method == 'POST':
        title = evaluation.title
        evaluation.delete()
        messages.success(request, f"Évaluation « {title} » supprimée.")
        if request.htmx:
            return HttpResponseClientRedirect(reverse('grades:grade_list'))
        return redirect('grades:grade_list')

    if request.htmx:
        return render(request, 'includes/delete_modal.html', {
            'object': evaluation,
            'modal_title': 'Supprimer cette évaluation',
            'modal_action': request.get_full_path(),
        })
    return render(request, 'grades/evaluation_confirm_delete.html', {
        'evaluation': evaluation,
    })


# --------------------------------------------------------------------------
# Saisie des notes par classe / matière
# --------------------------------------------------------------------------

@login_required
def grade_entry(request, evaluation=None):
    """
    Saisie des notes :
    1. L'utilisateur choisit classe + matière + période → liste des évaluations.
    2. Il choisit (ou crée) une évaluation → grille de saisie des notes.
    """
    classrooms = Class.objects.filter(is_active=True).order_by('name')
    subjects = Subject.objects.all().order_by('name')
    periods = Period.objects.select_related('academic_year').order_by('-academic_year', 'id')

    evaluation_obj = None
    evaluations = None
    rows = []

    evaluation_id = evaluation or request.GET.get('evaluation') \
        or request.POST.get('evaluation')

    # --- Enregistrement de la grille -----------------------------------
    if request.method == 'POST' and evaluation_id:
        evaluation_obj = get_object_or_404(
            Evaluation.objects.select_related('classroom', 'subject'),
            pk=evaluation_id,
        )
        saved, errors = 0, 0
        with transaction.atomic():
            for student in evaluation_obj.classroom.students.filter(is_active=True):
                raw = (request.POST.get(f'score_{student.id}') or '').strip().replace(',', '.')
                appr = (request.POST.get(f'appreciation_{student.id}') or '').strip()[:255]

                if raw == '':
                    score = None
                else:
                    try:
                        score = float(raw)
                        if score < 0 or score > float(evaluation_obj.max_score):
                            raise ValueError
                    except ValueError:
                        errors += 1
                        messages.warning(
                            request,
                            f"Note invalide pour {student.full_name} "
                            f"(doit être entre 0 et {evaluation_obj.max_score})."
                        )
                        continue

                Grade.objects.update_or_create(
                    student=student,
                    evaluation=evaluation_obj,
                    defaults={'score': score, 'appreciation': appr},
                )
                saved += 1

        if saved:
            messages.success(
                request,
                f"{saved} note(s) enregistrée(s) pour « {evaluation_obj.title} »."
            )
        return redirect('grades:grade_entry_eval', evaluation=evaluation_obj.pk)

    # --- Affichage -------------------------------------------------------
    if evaluation_id:
        evaluation_obj = get_object_or_404(
            Evaluation.objects.select_related('classroom', 'subject', 'period',
                                              'period__academic_year'),
            pk=evaluation_id,
        )
        grades_by_student = {
            g.student_id: g for g in Grade.objects.filter(evaluation=evaluation_obj)
        }
        rows = [
            {
                'student': s,
                'grade': grades_by_student.get(s.id),
            }
            for s in evaluation_obj.classroom.students.filter(is_active=True)
        ]
    else:
        classroom_id = request.GET.get('classroom')
        subject_id = request.GET.get('subject')
        period_id = request.GET.get('period')
        filters = {}
        if classroom_id:
            filters['classroom_id'] = classroom_id
        if subject_id:
            filters['subject_id'] = subject_id
        if period_id:
            filters['period_id'] = period_id
        if filters:
            evaluations = Evaluation.objects.filter(**filters).select_related(
                'classroom', 'subject', 'period'
            ).order_by('-date')

    context = {
        'classrooms': classrooms,
        'subjects': subjects,
        'periods': periods,
        'evaluation': evaluation_obj,
        'evaluations': evaluations,
        'rows': rows,
        'f_classroom': request.GET.get('classroom', ''),
        'f_subject': request.GET.get('subject', ''),
        'f_period': request.GET.get('period', ''),
    }
    return render(request, 'grades/grade_entry.html', context)


@login_required
def import_grades_excel(request):
    """Traitement du fichier Excel téléversé (matricule, note, appréciation)."""
    if request.method == 'POST':
        form = ExcelImportForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            evaluation = form.cleaned_data['evaluation']

            try:
                wb = openpyxl.load_workbook(excel_file, data_only=True)
                sheet = wb.active

                created_count = updated_count = 0
                errors = []

                with transaction.atomic():
                    for row_idx, row in enumerate(
                        sheet.iter_rows(min_row=2, values_only=True), start=2
                    ):
                        if not row or not row[0]:
                            continue

                        matricule = str(row[0]).strip()
                        raw_score = row[1] if len(row) > 1 else None
                        appreciation = str(row[2]).strip() if len(row) > 2 and row[2] is not None else ""

                        score = None
                        if raw_score is not None and str(raw_score).strip() != "":
                            try:
                                score = float(str(raw_score).replace(',', '.'))
                                if score < 0 or score > float(evaluation.max_score):
                                    errors.append(
                                        f"Ligne {row_idx}: note {score} hors barème "
                                        f"({evaluation.max_score})."
                                    )
                                    continue
                            except ValueError:
                                errors.append(
                                    f"Ligne {row_idx}: format de note invalide ('{raw_score}')."
                                )
                                continue

                        try:
                            student = Student.objects.get(student_id=matricule)
                        except Student.DoesNotExist:
                            errors.append(
                                f"Ligne {row_idx}: aucun élève avec le matricule '{matricule}'."
                            )
                            continue

                        grade, created = Grade.objects.update_or_create(
                            student=student,
                            evaluation=evaluation,
                            defaults={'score': score, 'appreciation': appreciation},
                        )
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1

                if created_count or updated_count:
                    messages.success(
                        request,
                        f"Importation réussie : {created_count} créée(s), "
                        f"{updated_count} mise(s) à jour."
                    )
                else:
                    messages.warning(request, "Aucune note importée.")
                for error in errors[:5]:
                    messages.warning(request, error)

            except Exception as e:
                messages.error(request, f"Erreur lors de la lecture du fichier : {e}")

            return redirect('grades:grade_list')

    return redirect('grades:grade_list')


# --------------------------------------------------------------------------
# Bulletins
# --------------------------------------------------------------------------

@login_required
def bulletin_select(request):
    """Choix de l'élève (ou de la classe) et de la période → bulletin."""
    students = Student.objects.filter(is_active=True).select_related('class_group')
    periods = Period.objects.select_related('academic_year').all()
    classrooms = Class.objects.filter(is_active=True)

    student_id = request.GET.get('student')
    period_id = request.GET.get('period')
    if student_id and period_id:
        return redirect('grades:student_report_card',
                        student_id=student_id, period_id=period_id)

    class_id = request.GET.get('classroom')
    if class_id and period_id:
        return redirect('grades:export_class_bulletins_pdf',
                        classroom_id=class_id, period_id=period_id)

    return render(request, 'grades/bulletin_select.html', {
        'students': students,
        'periods': periods,
        'classrooms': classrooms,
    })


@login_required
def student_report_card(request, student_id, period_id):
    """Bulletin détaillé d'un élève : moyennes par matière, rang, mention."""
    student = get_object_or_404(
        Student.objects.select_related('class_group', 'class_group__program'),
        pk=student_id,
    )
    period = get_object_or_404(Period.objects.select_related('academic_year'), pk=period_id)

    rows = subject_breakdown(student, period)
    general_avg = general_average(rows)

    rank = None
    total_ranked = 0
    class_avg = None
    if student.class_group:
        results, ranks, class_avg = class_ranking(student.class_group, period)
        rank = ranks.get(student.id)
        total_ranked = sum(1 for r in results if r['rank'] is not None)

    total_coef = sum(r['coefficient'] for r in rows)
    total_points = sum(r['points'] for r in rows if r['points'] is not None)

    school_setting = _school()
    context = {
        'student': student,
        'period': period,
        'school': school_setting,
        'rows': rows,
        'general_average': general_avg,
        'mention': mention_for(general_avg),
        'rank': rank,
        'total_ranked': total_ranked,
        'class_average': class_avg,
        'total_coef': total_coef,
        'total_points': round(total_points, 2),
    }
    context.update(_bulletin_header_context(school_setting))
    return render(request, 'grades/student_report_card.html', context)


@login_required
def export_bulletin_excel(request, student_id, period_id):
    """Export Excel du bulletin d'un élève."""
    student = get_object_or_404(
        Student.objects.select_related('class_group', 'class_group__program'),
        pk=student_id,
    )
    period = get_object_or_404(Period.objects.select_related('academic_year'), pk=period_id)

    rows = subject_breakdown(student, period)
    general_avg = general_average(rows)
    total_coef = sum(r['coefficient'] for r in rows)

    rank = class_avg = None
    total_ranked = 0
    if student.class_group:
        results, ranks, class_avg = class_ranking(student.class_group, period)
        rank = ranks.get(student.id)
        total_ranked = sum(1 for r in results if r['rank'] is not None)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Bulletin"

    school_setting = _school()
    ctx = _bulletin_header_context(school_setting)

    # --- Palette du design « aperçu » ---
    BLUE = '1D3557'; RED = 'E63946'; SUBBLUE = '457B9D'
    GRAY = '64748B'; LIGHT = 'F8F9FA'; TOTAL = 'E9ECEF'
    GREEN_BG, GREEN_FG = 'D1FAE5', '065F46'
    MID_BG, MID_FG = 'FEF3C7', '92400E'
    LOW_BG, LOW_FG = 'FEE2E2', 'B91C1C'
    thin = Side(style='thin', color='CBD5E1')
    border_all = Border(left=thin, right=thin, top=thin, bottom=thin)
    center = Alignment(horizontal='center', vertical='center', wrap_text=True)
    left_al = Alignment(horizontal='left', vertical='center', wrap_text=True)
    right_al = Alignment(horizontal='right', vertical='center')

    def F(size=9, bold=False, color='1E293B'):
        return Font(name='Arial', size=size, bold=bold, color=color)

    def fill(hex_color):
        return PatternFill(start_color=hex_color, end_color=hex_color, fill_type='solid')

    # --- En-tête : école (gauche) | titre rouge (droite) ---
    ws.merge_cells('A1:C1')
    ws['A1'] = ctx['school_name']
    ws['A1'].font = F(13, True, BLUE)
    ws['A2'] = ' · '.join(p for p in (
        ctx['school_address'],
        f"Tél : {ctx['school_phone']}" if ctx['school_phone'] else None) if p)
    ws.merge_cells('A2:C2')
    ws['A2'].font = F(8, False, GRAY)

    ws.merge_cells('D1:E1')
    ws['D1'] = 'Bulletin de notes'
    ws['D1'].font = F(12, True, RED)
    ws['D1'].alignment = right_al
    ws.merge_cells('D2:E2')
    ws['D2'] = f"{period.name} — Année {period.academic_year.name}"
    ws['D2'].font = F(9, True, SUBBLUE)
    ws['D2'].alignment = right_al

    # Trait de séparation bleu sous l'en-tête
    for col in 'ABCDE':
        ws[f'{col}2'].border = Border(bottom=Side(style='medium', color=BLUE))
    ws.row_dimensions[1].height = 20

    # --- Encadré élève ---
    ws.merge_cells('A4:B4')
    ws['A4'] = f"Élève : {student.last_name} {student.first_name}"
    ws['A4'].font = F(9, True)
    ws.merge_cells('C4:D4')
    ws['C4'] = f"Matricule : {student.student_id}"
    ws['C4'].font = F(9)
    ws['E4'] = f"Classe : {student.class_group.name if student.class_group else 'N/A'}"
    ws['E4'].font = F(9)
    ws.merge_cells('A5:B5')
    ws['A5'] = f"Effectif classé : {total_ranked if total_ranked else '—'}"
    ws['A5'].font = F(9)
    for r in (4, 5):
        for col in 'ABCDE':
            c = ws[f'{col}{r}']
            c.fill = fill(LIGHT)
        ws[f'A{r}'].border = Border(left=Side(style='medium', color=BLUE))
    ws.row_dimensions[4].height = 16
    ws.row_dimensions[5].height = 16

    # --- Tableau des notes ---
    header_row = 7
    headers = ["MATIÈRE", "COEFFICIENT", "MOYENNE / 20", "POINTS (MOY × COEF)", "APPRÉCIATION"]
    for col_num, h in enumerate(headers, start=1):
        c = ws.cell(row=header_row, column=col_num)
        c.value = h
        c.font = F(8, True, 'FFFFFF')
        c.fill = fill(BLUE)
        c.alignment = center if col_num > 1 else left_al
        c.border = border_all
    ws.row_dimensions[header_row].height = 17

    current_row = header_row + 1

    def pill_cell(cell, average):
        """Pastille de couleur selon la moyenne (comme l'aperçu web)."""
        if average is None:
            cell.value = '—'
        else:
            cell.value = average
            if average >= 14:
                cell.fill, cell.font = fill(GREEN_BG), F(9, True, GREEN_FG)
            elif average >= 10:
                cell.fill, cell.font = fill(MID_BG), F(9, True, MID_FG)
            else:
                cell.fill, cell.font = fill(LOW_BG), F(9, True, LOW_FG)
        cell.alignment = center
        cell.border = border_all

    for row in rows:
        ws.cell(row=current_row, column=1, value=row['subject'].name).font = F(9, True)
        ws.cell(row=current_row, column=1).alignment = left_al
        ws.cell(row=current_row, column=1).border = border_all
        ws.cell(row=current_row, column=2, value=row['coefficient'])
        ws.cell(row=current_row, column=3, value=row['average'])
        pill_cell(ws.cell(row=current_row, column=3), row['average'])
        for col_num, val in ((4, row['points'] if row['points'] is not None else '—'),
                             (5, row['appreciation'] or '—')):
            c = ws.cell(row=current_row, column=col_num, value=val)
            c.font = F(9)
            c.alignment = center if col_num == 4 else left_al
            c.border = border_all
        ws.cell(row=current_row, column=2).alignment = center
        ws.cell(row=current_row, column=2).border = border_all
        current_row += 1

    total_points = round(sum(r['points'] for r in rows if r['points']), 2)
    for col_num, val in enumerate(["TOTAL", total_coef, '—', total_points, '—'], start=1):
        c = ws.cell(row=current_row, column=col_num, value=val)
        c.font = F(9, True)
        c.fill = fill(TOTAL)
        c.alignment = center if col_num > 1 else left_al
        c.border = border_all
    current_row += 1

    # MOYENNE GÉNÉRALE (bandeau bleu)
    ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=2)
    ws.cell(row=current_row, column=1, value="MOYENNE GÉNÉRALE").font = F(10, True, 'FFFFFF')
    ws.cell(row=current_row, column=1).alignment = left_al
    ws.cell(row=current_row, column=3,
            value=f"{general_avg} / 20" if general_avg is not None else 'N/A')
    ws.cell(row=current_row, column=3).font = F(10, True, 'FFFFFF')
    ws.cell(row=current_row, column=3).alignment = center
    ws.merge_cells(start_row=current_row, start_column=4, end_row=current_row, end_column=5)
    ws.cell(row=current_row, column=4, value=mention_for(general_avg)).font = F(10, True, 'FFFFFF')
    ws.cell(row=current_row, column=4).alignment = center
    for col in range(1, 6):
        ws.cell(row=current_row, column=col).fill = fill(BLUE)
    ws.row_dimensions[current_row].height = 20
    current_row += 2

    # --- 4 cartes : Moyenne générale / Rang / Moyenne classe / Mention ---
    cards = [
        (1, 1, 'MOYENNE GÉNÉRALE', general_avg if general_avg is not None else '—', True),
        (2, 2, 'RANG', f"{rank}/{total_ranked}" if rank else '—', False),
        (3, 3, 'MOYENNE DE LA CLASSE', class_avg if class_avg is not None else '—', False),
        (4, 5, 'MENTION', mention_for(general_avg), False),
    ]
    label_row, value_row = current_row, current_row + 1
    for col_start, col_end, label, value, is_green in cards:
        if col_end > col_start:
            ws.merge_cells(start_row=label_row, start_column=col_start,
                           end_row=label_row, end_column=col_end)
            ws.merge_cells(start_row=value_row, start_column=col_start,
                           end_row=value_row, end_column=col_end)
        lc = ws.cell(row=label_row, column=col_start, value=label)
        lc.font = F(7, True, GRAY)
        lc.alignment = center
        vc = ws.cell(row=value_row, column=col_start, value=value)
        vc.font = F(12, True, '059669' if is_green else BLUE)
        vc.alignment = center
        for r in (label_row, value_row):
            for cc in range(col_start, col_end + 1):
                ws.cell(row=r, column=cc).border = border_all
                ws.cell(row=r, column=cc).fill = fill(LIGHT)
    ws.row_dimensions[value_row].height = 22
    current_row = value_row + 2

    # --- Signatures ---
    sig_row = current_row
    ws.merge_cells(start_row=sig_row, start_column=1, end_row=sig_row, end_column=2)
    ws.cell(row=sig_row, column=1, value="Signature du Chef d'établissement :").font = F(8, False, '334155')
    ws.merge_cells(start_row=sig_row, start_column=4, end_row=sig_row, end_column=5)
    ws.cell(row=sig_row, column=4, value="Signature du Parent / Tuteur :").font = F(8, False, '334155')
    line_row = sig_row + 3
    for col_start, col_end in ((1, 2), (4, 5)):
        ws.merge_cells(start_row=line_row, start_column=col_start,
                       end_row=line_row, end_column=col_end)
        for cc in range(col_start, col_end + 1):
            ws.cell(row=line_row, column=cc).border = Border(top=Side(style='thin', color=GRAY))
    current_row = line_row + 2

    # --- Pied de page ---
    ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=5)
    foot = ws.cell(row=current_row, column=1)
    foot.value = (f"Bulletin généré le {timezone.localtime().strftime('%d/%m/%Y %H:%M')}"
                  f" — {ctx['school_name']}")
    foot.font = F(7, False, '94A3B8')
    foot.alignment = center

    # --- Largeurs + impression A5 ---
    for col, w in {'A': 24, 'B': 12, 'C': 13, 'D': 15, 'E': 24}.items():
        ws.column_dimensions[col].width = w
    from openpyxl.worksheet.page import PageMargins
    from openpyxl.worksheet.properties import PageSetupProperties
    ws.page_setup.paperSize = 11  # A5
    ws.page_setup.orientation = 'portrait'
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.page_margins = PageMargins(left=0.35, right=0.35, top=0.45, bottom=0.45)
    ws.print_area = f'A1:E{current_row}'

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    safe_name = student.last_name or 'eleve'
    response['Content-Disposition'] = (
        f'attachment; filename="Bulletin_{safe_name}_{period.name}.xlsx"'
    )
    wb.save(response)
    return response


@login_required
def export_bulletin_pdf(request, student_id, period_id):
    """Export PDF du bulletin d'un élève (xhtml2pdf)."""
    student = get_object_or_404(
        Student.objects.select_related('class_group', 'class_group__program'),
        pk=student_id,
    )
    period = get_object_or_404(Period.objects.select_related('academic_year'), pk=period_id)

    rows = subject_breakdown(student, period)
    general_avg = general_average(rows)

    rank = total_ranked = class_avg = None
    if student.class_group:
        results, ranks, class_avg = class_ranking(student.class_group, period)
        rank = ranks.get(student.id)
        total_ranked = sum(1 for r in results if r['rank'] is not None)

    school_setting = _school()
    context = {
        'school': school_setting,
        'student': student,
        'period': period,
        'rows': rows,
        'general_average': general_avg,
        'mention': mention_for(general_avg),
        'rank': rank,
        'total_ranked': total_ranked,
        'class_average': class_avg,
        'total_coef': sum(r['coefficient'] for r in rows),
        'total_points': round(sum(r['points'] for r in rows if r['points']), 2),
    }
    context.update(_bulletin_header_context(school_setting))
    filename = f"Bulletin_{student.student_id}_{period.name}.pdf"
    return _render_pdf('grades/report_card_pdf.html', context, filename)


@login_required
def export_class_bulletins_pdf(request, classroom_id, period_id):
    """Export PDF de tous les bulletins d'une classe (un par page)."""
    classroom = get_object_or_404(
        Class.objects.select_related('program'), pk=classroom_id
    )
    period = get_object_or_404(Period.objects.select_related('academic_year'), pk=period_id)

    results, ranks, class_avg = class_ranking(classroom, period)

    bulletins = []
    for item in results:
        student = item['student']
        rows = subject_breakdown(student, period)
        bulletins.append({
            'student': student,
            'rows': rows,
            'general_average': item['average'],
            'rank': item['rank'],
            'mention': mention_for(item['average']),
            'total_coef': sum(r['coefficient'] for r in rows),
            'total_points': round(sum(r['points'] for r in rows if r['points']), 2),
        })

    school_setting = _school()
    context = {
        'school': school_setting,
        'classroom': classroom,
        'period': period,
        'class_average': class_avg,
        'bulletins': bulletins,
    }
    context.update(_bulletin_header_context(school_setting))
    filename = f"Bulletins_{classroom.name}_{period.name}.pdf"
    return _render_pdf('grades/class_bulletins_pdf.html', context, filename)

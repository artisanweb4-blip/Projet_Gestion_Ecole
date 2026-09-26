from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
import openpyxl
from students.models import Student

from .models import Student, Period, Evaluation, Grade
from .forms import ExcelImportForm, GradeForm


def grade_list(request):
    """Vue principale affichant la liste des évaluations et le formulaire d'import"""
    evaluations = Evaluation.objects.select_related('classroom', 'subject', 'period').all()
    form = ExcelImportForm()
    
    context = {
        'evaluations': evaluations,
        'form': form,
    }
    return render(request, 'grades/grade_list.html', context)


def import_grades_excel(request):
    """Traitement du fichier Excel téléversé"""
    if request.method == 'POST':
        form = ExcelImportForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            evaluation = form.cleaned_data['evaluation']

            try:
                wb = openpyxl.load_workbook(excel_file, data_only=True)
                sheet = wb.active

                created_count = 0
                updated_count = 0
                errors = []

                with transaction.atomic():
                    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                        if not row or not row[0]:
                            continue

                        matricule = str(row[0]).strip()
                        raw_score = row[2] if len(row) > 2 else None
                        appreciation = str(row[3]).strip() if len(row) > 3 and row[3] is not None else ""

                        score = None
                        if raw_score is not None and str(raw_score).strip() != "":
                            try:
                                score = float(raw_score)
                                if score < 0 or score > evaluation.max_score:
                                    errors.append(f"Ligne {row_idx}: Note {score} hors barème ({evaluation.max_score}).")
                                    continue
                            except ValueError:
                                errors.append(f"Ligne {row_idx}: Format de note invalide ('{raw_score}').")
                                continue

                        try:
                            student = Student.objects.get(matricule=matricule)
                        except Student.DoesNotExist:
                            errors.append(f"Ligne {row_idx}: Aucun élève avec le matricule '{matricule}'.")
                            continue

                        grade, created = Grade.objects.update_or_create(
                            student=student,
                            evaluation=evaluation,
                            defaults={'score': score, 'appreciation': appreciation}
                        )

                        if created:
                            created_count += 1
                        else:
                            updated_count += 1

                if created_count > 0 or updated_count > 0:
                    messages.success(request, f"Importation réussie : {created_count} créée(s), {updated_count} mise(s) à jour.")
                
                for error in errors[:5]:
                    messages.warning(request, error)

            except Exception as e:
                messages.error(request, f"Erreur lors de la lecture du fichier : {str(e)}")

            return redirect('grades:grade_list')
    else:
        form = ExcelImportForm()

    return render(request, 'grades/grade_list.html', {'form': form})


def student_report_card(request, student_id, period_id):
    """Affichage du bulletin de notes d'un élève"""
    student = get_object_or_404(Student, pk=student_id)
    period = get_object_or_404(Period, pk=period_id)

    overall_average = student.get_period_average(period.id)
    grades = student.grades.filter(evaluation__period=period).select_related('evaluation', 'evaluation__subject')

    context = {
        'student': student,
        'period': period,
        'overall_average': overall_average,
        'grades': grades,
    }
    return render(request, 'grades/report_card.html', context)

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Avg
from students.models import Student
from .models import Period, Grade

def export_bulletin_excel(request, student_id, period_id):
    student = get_object_or_404(Student, pk=student_id)
    period = get_object_or_404(Period, pk=period_id)
    
    grades = Grade.objects.filter(
        student=student, 
        evaluation__period=period
    ).select_related('evaluation__subject')
    
    overall_average = grades.aggregate(Avg('score'))['score__avg']

    # Création du classeur Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Bulletin"

    # Styles
    font_header = Font(name='Arial', size=14, bold=True, color='1D3557')
    font_sub = Font(name='Arial', size=11, bold=True)
    font_th = Font(name='Arial', size=10, bold=True, color='FFFFFF')
    fill_th = PatternFill(start_color='1D3557', end_color='1D3557', fill_type='solid')
    fill_total = PatternFill(start_color='E9ECEF', end_color='E9ECEF', fill_type='solid')
    thin_border = Border(
        left=Side(style='thin', color='DEE2E6'),
        right=Side(style='thin', color='DEE2E6'),
        top=Side(style='thin', color='DEE2E6'),
        bottom=Side(style='thin', color='DEE2E6')
    )

    # Entête du document
    ws['A1'] = "BULLETIN DE NOTES"
    ws['A1'].font = font_header
    ws['A2'] = f"Période : {period.name}"
    ws['A2'].font = font_sub

    # Informations de l'élève
    ws['A4'] = f"Élève : {student.last_name.upper()} {student.first_name}"
    ws['A5'] = f"Classe : {student.classroom.name if student.classroom else 'N/A'}"
    ws['D4'] = f"Matricule : {student.registration_number or student.id}"
    ws['D5'] = "Année Scolaire : 2025 - 2026"

    # En-têtes du tableau
    headers = ["Matière", "Coefficient", "Note / 20", "Total (Note × Coeff)"]
    ws.append([]) # Ligne vide (ligne 6)
    ws.append(headers) # Ligne 7

    for col_num in range(1, 5):
        cell = ws.cell(row=7, column=col_num)
        cell.font = font_th
        cell.fill = fill_th
        cell.alignment = Alignment(horizontal='center' if col_num > 1 else 'left')

    # Remplissage des notes
    current_row = 8
    for grade in grades:
        coeff = grade.evaluation.subject.coefficient if hasattr(grade.evaluation.subject, 'coefficient') else 1
        score = grade.score if grade.score is not None else 0
        total = score * coeff if grade.score is not None else "-"

        ws.append([
            grade.evaluation.subject.name,
            coeff,
            score if grade.score is not None else "N/A",
            total
        ])
        
        for col_num in range(1, 5):
            cell = ws.cell(row=current_row, column=col_num)
            cell.border = thin_border
            if col_num > 1:
                cell.alignment = Alignment(horizontal='center')
        current_row += 1

    # Ligne de Moyenne Générale
    avg_display = round(overall_average, 2) if overall_average is not None else "N/A"
    ws.append(["MOYENNE GÉNÉRALE", "-", avg_display, "-"])
    
    for col_num in range(1, 5):
        cell = ws.cell(row=current_row, column=col_num)
        cell.font = Font(bold=True)
        cell.fill = fill_total
        cell.border = thin_border
        if col_num > 1:
            cell.alignment = Alignment(horizontal='center')

    # Ajustement automatique de la largeur des colonnes
    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 22

    # Préparation de la réponse HTTP Excel
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    filename = f"Bulletin_{student.last_name}_{period.name}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response

from django.shortcuts import render, redirect
from students.models import Student
from .models import Period

def bulletin_select(request):
    """Vue pour choisir l'élève et la période avant de générer le bulletin."""
    students = Student.objects.select_related('classroom').all()
    periods = Period.objects.all()
    
    student_id = request.GET.get('student')
    period_id = request.GET.get('period')
    
    if student_id and period_id:
        return redirect('grades:student_report_card', student_id=student_id, period_id=period_id)
        
    context = {
        'students': students,
        'periods': periods,
    }
    return render(request, 'grades/bulletin_select.html', context)

def bulletin_select(request):
    """
    Vue de sélection d'un élève et d'une période pour générer le bulletin.
    """
    # Utilisation du bon nom de champ : class_group
    students = Student.objects.select_related('class_group').all()
    periods = Period.objects.all()
    
    student_id = request.GET.get('student')
    period_id = request.GET.get('period')
    
    if student_id and period_id:
        return redirect('grades:student_report_card', student_id=student_id, period_id=period_id)
        
    context = {
        'students': students,
        'periods': periods,
    }
    return render(request, 'notes/bulletin_select.html', context)
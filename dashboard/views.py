"""
Tableau de bord : KPIs, activités récentes et graphiques.
"""
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render
from django.utils import timezone

from classes.models import Class
from courses.models import Subject
from grades.models import Evaluation, Grade, Period
from finance.models import StudentPayment
from school_calendar.models import AcademicEvent
from school_settings.models import SchoolSetting
from students.models import Student
from teachers.models import Teacher


@login_required
def dashboard_home(request):
    """Page d'accueil : indicateurs clés de l'établissement."""
    total_students = Student.objects.filter(is_active=True).count()
    total_teachers = Teacher.objects.filter(is_active=True).count()
    total_classes = Class.objects.filter(is_active=True).count()
    total_subjects = Subject.objects.filter(is_active=True).count()

    payments_agg = StudentPayment.objects.aggregate(total=Sum('amount_paid'))
    total_payments = payments_agg['total'] or 0

    recent_students = Student.objects.filter(is_active=True).select_related('class_group')[:5]
    recent_payments = StudentPayment.objects.select_related('student')[:5]
    recent_evaluations = Evaluation.objects.select_related(
        'classroom', 'subject', 'period'
    )[:5]

    today = timezone.localdate()
    try:
        upcoming_events = AcademicEvent.objects.filter(
            end_date__gte=today
        ).order_by('start_date')[:5]
    except Exception:
        upcoming_events = []

    # Année académique & période active (module grades)
    active_year = Period.objects.select_related('academic_year').values_list(
        'academic_year__name', flat=True
    ).first() or "—"

    # --- Graphique : moyenne générale par classe (1 seule requête SQL) ----
    from django.db.models import Avg, ExpressionWrapper, F, FloatField
    note20 = ExpressionWrapper(
        F('score') * 20.0 / F('evaluation__max_score'),
        output_field=FloatField(),
    )
    class_rows = (
        Grade.objects
        .filter(score__isnull=False,
                student__is_active=True,
                student__class_group__isnull=False)
        .annotate(note20=note20)
        .values('student__class_group_id', 'student__class_group__name')
        .annotate(average=Avg('note20'))
        .order_by('student__class_group__name')
    )
    class_stats = [
        {
            'name': row['student__class_group__name'],
            'average': round(row['average'], 2),
            'percent': max(2, min(100, round(row['average'] * 5))),
        }
        for row in class_rows
    ]

    context = {
        'kpi_students': total_students,
        'kpi_teachers': total_teachers,
        'kpi_classes': total_classes,
        'kpi_subjects': total_subjects,
        'kpi_payments': total_payments,
        'recent_students': recent_students,
        'recent_payments': recent_payments,
        'recent_evaluations': recent_evaluations,
        'upcoming_events': upcoming_events,
        'active_year': active_year,
        'class_stats': class_stats,
    }
    return render(request, 'dashboard/dashboard.html', context)

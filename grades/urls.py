# grades/urls.py
from django.urls import path

from . import views

app_name = 'grades'

urlpatterns = [
    # Liste des évaluations & import Excel
    path('', views.grade_list, name='grade_list'),
    path('import-excel/', views.import_grades_excel, name='import_excel'),

    # Saisie des notes par classe / matière
    path('entry/', views.grade_entry, name='grade_entry'),
    path('entry/<int:evaluation>/', views.grade_entry, name='grade_entry_eval'),
    path('evaluations/add/', views.evaluation_create, name='evaluation_create'),
    path('evaluations/<int:pk>/edit/', views.evaluation_edit, name='evaluation_edit'),
    path('evaluations/<int:pk>/delete/', views.evaluation_delete, name='evaluation_delete'),

    # Bulletins
    path('bulletins/', views.bulletin_select, name='bulletin_select'),
    path(
        'bulletins/class/<int:classroom_id>/period/<int:period_id>/export-pdf/',
        views.export_class_bulletins_pdf,
        name='export_class_bulletins_pdf',
    ),
    path('student/<int:student_id>/report/<int:period_id>/',
         views.student_report_card, name='student_report_card'),
    path('student/<int:student_id>/report/<int:period_id>/export-excel/',
         views.export_bulletin_excel, name='export_bulletin_excel'),
    path('student/<int:student_id>/report/<int:period_id>/export-pdf/',
         views.export_bulletin_pdf, name='export_bulletin_pdf'),
]

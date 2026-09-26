# grades/urls.py
from django.urls import path
from . import views

# Cette ligne est OBLIGATOIRE pour utiliser le namespace 'grades:...'
app_name = 'grades'

urlpatterns = [
    path('', views.grade_list, name='grade_list'),
    path('import-excel/', views.import_grades_excel, name='import_excel'),

    path('bulletins/', views.bulletin_select, name='bulletin_select'),
    path('student/<int:student_id>/report/<int:period_id>/', views.student_report_card, name='student_report_card'),
    path('student/<int:student_id>/report/<int:period_id>/export-excel/', views.export_bulletin_excel, name='export_bulletin_excel'),
]

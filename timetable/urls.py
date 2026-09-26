from django.urls import path
from . import views

app_name = 'timetable'

urlpatterns = [
    # Redirige 'index' vers votre vue principale d'emploi du temps
    path('', views.timetable_view, name='index'),
    path('grid/', views.timetable_view, name='grid'),
    path('timeslot/<int:pk>/delete/', views.timeslot_delete_view, name='timeslot_delete'),
    path('ajax/subjects/', views.ajax_get_subjects_by_class, name='ajax_get_subjects_by_class'),
]
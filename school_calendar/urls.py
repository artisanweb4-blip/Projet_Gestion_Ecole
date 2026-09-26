from django.urls import path
from . import views

app_name = 'school_calendar'

urlpatterns = [
    # Vue du Calendrier FullCalendar
    path('', views.academic_calendar_view, name='calendar'),
    # Vue de la Liste (qui gère l'affichage, les filtres ET l'édition via modale)
    path('list/', views.academic_calendar_list_view, name='calendar_list'),
    # API pour FullCalendar
    path(
        'api/events/',
        views.academic_calendar_events_api,
        name='api_academic_events',
    ),
    # Suppression d'un événement
    path(
        'event/<int:pk>/delete/',
        views.academic_event_delete_view,
        name='event_delete',
    ),
]
# school_settings/urls.py
from django.urls import path
from . import views

app_name = 'school_settings'

urlpatterns = [
    path('', views.settings_index, name='index'),
    path('general/', views.settings_general, name='general'),
    path('school/', views.settings_school, name='school'),
    path('notifications/', views.settings_notifications, name='notifications'),
    path('users/', views.settings_users, name='users'),
    path('backup/', views.settings_backup, name='backup'),
    path('security/', views.settings_security, name='security'),

    path('backup/download/', views.download_backup, name='download_backup'),
]
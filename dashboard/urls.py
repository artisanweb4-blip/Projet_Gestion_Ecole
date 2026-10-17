from django.urls import path

from . import views

# Pas d'app_name : les noms 'dashboard' et 'home' restent globaux.
# La racine '/' est la landing page publique (app website).

urlpatterns = [
    path('dashboard/', views.dashboard_home, name='dashboard'),
    path('home/', views.dashboard_home, name='home'),
]

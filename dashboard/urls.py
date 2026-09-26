from django.urls import path

from . import views

# Pas d'app_name : les noms 'home' et 'dashboard' restent globaux
# (utilisés par LOGIN_REDIRECT_URL et core.mixins.RoleRequiredMixin).

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('dashboard/', views.dashboard_home, name='dashboard'),
]

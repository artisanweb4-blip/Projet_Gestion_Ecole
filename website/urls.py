from django.urls import path

from . import platform_views, views

urlpatterns = [
    # Pages publiques
    path('', views.landing, name='landing'),
    path('register/school/', views.register_school, name='register_school'),

    # Plateforme Super Admin
    path('platform/', platform_views.PlatformDashboardView.as_view(), name='platform_dashboard'),
    path('platform/schools/add/', platform_views.PlatformSchoolCreateView.as_view(), name='platform_school_add'),
    path('platform/schools/<int:pk>/', platform_views.PlatformSchoolDetailView.as_view(), name='platform_school_detail'),
    path('platform/schools/<int:pk>/toggle/', platform_views.PlatformSchoolToggleView.as_view(), name='platform_school_toggle'),
    path('platform/schools/<int:pk>/delete/', platform_views.PlatformSchoolDeleteView.as_view(), name='platform_school_delete'),
    path('platform/users/', platform_views.PlatformUsersView.as_view(), name='platform_users'),
]

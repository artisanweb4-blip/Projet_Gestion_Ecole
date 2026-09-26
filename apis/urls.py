"""
Routeur API master (/api/).

Seuls les vrais endpoints DRF sont exposés ici. Les modules « web »
(students, teachers, classes, courses...) sont servis par leurs propres
URLs en tête du projet (voir django_config/urls.py). L'authentification
JWT est disponible sous /accounts/auth/login/ et /accounts/auth/refresh/.
"""
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Documentation OpenAPI (Swagger & ReDoc)
    path('docs/', SpectacularAPIView.as_view(), name='api-schema'),
    path('docs/swagger/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-swagger'),
    path('docs/redoc/', SpectacularRedocView.as_view(url_name='api-schema'), name='api-redoc'),

    # Modules API
    path('v1/finance/', include('finance.urls')),
    path('v1/admissions/', include('admissions.urls')),
    path('v1/assignments/', include('assignments.urls')),
    path('v1/exams/', include('exams.urls')),
    path('v1/trs/', include('trs.urls')),
]

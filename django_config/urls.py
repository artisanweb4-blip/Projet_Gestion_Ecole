"""
URL configuration for django_config project (Gestion d'École).
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views

from accounts import views as accounts_views
from django.urls import include, path

urlpatterns = [
    # Administration Django
    path('admin/', admin.site.urls),

    # Site public (landing + inscription école) & plateforme super admin
    path('', include('website.urls')),

    # Tableau de bord
    path('', include('dashboard.urls')),

    # Authentification (session web)
    path('accounts/login/', accounts_views.SchoolLoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True,
    ), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # API REST (JWT)
    path('accounts/', include('accounts.urls')),
    path('api/', include('apis.urls')),

    # Modules web
    path('students/', include('students.urls')),
    path('teachers/', include('teachers.urls')),
    path('parents/', include('parents.urls')),
    path('classes/', include('classes.urls')),
    path('courses/', include('courses.urls')),
    path('grades/', include('grades.urls')),
    path('accounting/', include('accounting.urls')),
    path('timetable/', include('timetable.urls')),
    path('calendar/', include('school_calendar.urls')),
    path('settings/', include('school_settings.urls')),
    path('documents/', include('documents.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

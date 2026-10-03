"""
Django settings for django_config project (Gestion d'École - GCE).
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-gce-dev-key-change-me-in-production'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

_allowed_hosts = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0')
ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts.split(',') if h.strip()]
if DEBUG and '*' not in ALLOWED_HOSTS:
    # En développement / prévisualisation, on accepte tous les hôtes.
    ALLOWED_HOSTS.append('*')

# Origines de confiance (CSRF) — nécessaire derrière un proxy de prévisualisation.
_csrf_origins = os.getenv(
    'CSRF_TRUSTED_ORIGINS',
    'https://localhost,http://localhost,https://*.e2b.app'
)
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(',') if o.strip()]

# Application definition

INSTALLED_APPS = [
    # Core / Django standard apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'django_htmx',
    'django.contrib.humanize',
    'crispy_forms',
    'crispy_bootstrap5',
    'drf_spectacular',

    # Project apps
    'core',
    'accounting',   # Comptabilité (frais & paiements)
    'accounts',        # Utilisateurs / rôles / JWT
    'dashboard',       # Tableau de bord
    'students',        # Élèves
    'teachers',        # Enseignants
    'parents',         # Parents d'élèves
    'classes',         # Classes
    'courses',         # Matières, programmes & cours
    'grades',          # Notes, évaluations & bulletins
    'timetable',       # Emploi du temps (grille)
    'trs',             # Planification des séances (API)
    'school_calendar', # Calendrier académique
    'school_settings', # Paramètres de l'établissement
    'documents',       # Documents scolaires (certificats, PDF)
    'finance',         # Frais & paiements (API)
    'admissions',      # Demandes d'admission (API)
    'assignments',     # Devoirs (API)
    'exams',           # Examens (API)
    'analytics',       # Analytique (visites de la plateforme)
]

MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',   # Réponses compressées (plus rapide)
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Fichiers statiques compressés & cachés
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.scoping.CurrentSchoolMiddleware',
    'analytics.middleware.VisitTrackingMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'django_config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.global_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'django_config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

_db_engine = os.getenv('DB_ENGINE', 'sqlite3')

if _db_engine in ('sqlite', 'sqlite3', 'django.db.backends.sqlite3'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'CONN_MAX_AGE': 60,  # Connexion persistante : pas de reconnexion à chaque page
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'school_db'),
            'USER': os.getenv('DB_USER', 'school_user'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'school_password'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }


# Authentication

AUTH_USER_MODEL = 'accounts.User'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Django REST Framework & JWT

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', '60'))
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME_DAYS', '7'))
    ),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

SPECTACULAR_SETTINGS = {
    'TITLE': "API - Gestion d'École (GCE)",
    'DESCRIPTION': "API REST du système de gestion scolaire (élèves, notes, bulletins, finances).",
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# Crispy Forms (Bootstrap 5)
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Douala'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

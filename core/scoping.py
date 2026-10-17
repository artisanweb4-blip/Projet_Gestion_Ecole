"""
Isolation des données par école (multi-établissements).

Principe :
- Chaque utilisateur (non superadmin) appartient à une école (User.school).
- Un gestionnaire (SchoolManager) filtre AUTOMATIQUEMENT toutes les requêtes
  des modèles « sensibles » selon l'école de l'utilisateur connecté :
  listes, fiches, modifications, suppressions, exports, PDF...
- Les superadministrateurs de la plateforme (is_superuser) voient TOUT.
- À la création d'un objet lié à une école, la clé est attribuée
  automatiquement (assign_school / HtmxCrudMixin).
- Une école suspendue (is_active=False) n'accède plus à aucune donnée
  et la connexion est bloquée (voir middleware + vue de connexion).
"""
import threading

from django.core.exceptions import FieldDoesNotExist
from django.db import models


class _NoAccess:
    """Sentinelle : l'utilisateur ne doit voir AUCUNE donnée."""

    def __repr__(self):
        return "NO_ACCESS"


NO_ACCESS = _NoAccess()

_local = threading.local()


def set_current_school(school):
    """Mémorise l'école du contexte de la requête courante (thread-local)."""
    _local.current_school = school


def get_current_school():
    """École du contexte courant (None = hors requête / superadmin / anonyme)."""
    return getattr(_local, 'current_school', None)


def assign_school(instance, user):
    """Attribue l'école de l'utilisateur à une instance nouvellement créée."""
    if instance is None or getattr(instance, 'school_id', None) is not None:
        return
    try:
        instance._meta.get_field('school')
    except FieldDoesNotExist:
        return
    if user is not None and user.is_authenticated and getattr(user, 'school_id', None):
        instance.school_id = user.school_id


class SchoolManager(models.Manager):
    """Gestionnaire filtrant automatiquement par l'école courante.

    - Si le modèle possède un champ « school » : filtre direct.
    - Sinon, le chemin de jointure est défini via `scope_path`
      (ex. 'student__school' pour une note).
    - Sans contexte d'école (superadmin, anonyme, commandes) : aucune limite.
    """

    scope_path = None

    def get_queryset(self):
        qs = super().get_queryset()
        school = get_current_school()
        if school is None:
            return qs
        if school == NO_ACCESS:
            return qs.none()
        model = self.model
        try:
            model._meta.get_field('school')
        except FieldDoesNotExist:
            if not self.scope_path:
                return qs
            return qs.filter(**{self.scope_path: school})
        return qs.filter(school=school)


def scoped_manager(path=None):
    """Fabrique un gestionnaire d'école avec un chemin de jointure donné."""

    class _ScopedSchoolManager(SchoolManager):
        pass

    _ScopedSchoolManager.scope_path = path
    return _ScopedSchoolManager()


class CurrentSchoolMiddleware:
    """Pose l'école courante pour chaque requête (après AuthenticationMiddleware).

    - Superutilisateur ou anonyme : aucune restriction (plateforme / site public).
    - Utilisateur d'une école : ses données uniquement.
    - Utilisateur sans école ou école suspendue : aucune donnée (NO_ACCESS).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    # Préfixes accessibles au Super Admin (interface plateforme uniquement)
    SUPERADMIN_ALLOWED = (
        '/platform', '/accounts', '/admin', '/api/',
        '/static', '/media', '/favicon', '/robots.txt', '/sitemap.xml',
    )

    def __call__(self, request):
        set_current_school(None)

        user = getattr(request, 'user', None)

        # Interfaces séparées : le Super Admin utilise UNIQUEMENT /platform.
        if (user is not None and user.is_authenticated and user.is_superuser
                and not request.path.startswith(self.SUPERADMIN_ALLOWED)):
            from django.shortcuts import redirect
            return redirect('platform_dashboard')

        if user is not None and user.is_authenticated and not user.is_superuser:
            school = getattr(user, 'school', None)
            if school is not None and school.is_active:
                set_current_school(school)
            else:
                set_current_school(NO_ACCESS)

        try:
            return self.get_response(request)
        finally:
            set_current_school(None)

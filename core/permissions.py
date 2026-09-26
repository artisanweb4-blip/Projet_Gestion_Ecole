from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminUserRole(BasePermission):
    """Permission réservée aux administrateurs de l'école."""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.role == 'ADMIN' or request.user.is_superuser)
        )

class IsTeacherUserRole(BasePermission):
    """Permission réservée aux enseignants ou administrateurs."""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.role in ['TEACHER', 'ADMIN'] or request.user.is_superuser)
        )

class IsStudentUserRole(BasePermission):
    """Permission réservée aux étudiants (ou lecture seule)."""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['STUDENT', 'ADMIN']
        )

class IsParentUserRole(BasePermission):
    """Permission réservée aux parents d'élèves."""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['PARENT', 'ADMIN']
        )

class ReadOnlyOrAdmin(BasePermission):
    """Accès en lecture pour tous les utilisateurs authentifiés, écriture réservée à l'Admin."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated and (request.user.role == 'ADMIN' or request.user.is_superuser))

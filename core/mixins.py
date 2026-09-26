from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.contrib import messages

class RoleRequiredMixin(AccessMixin):
    """
    Mixin qui vérifie si l'utilisateur possède l'un des rôles autorisés.
    Autorise systématiquement les superutilisateurs (is_superuser=True).
    """
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        # 1. Vérifier si l'utilisateur est connecté
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # 2. Les superutilisateurs ont TOUS les droits par défaut
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        # 3. Récupération et normalisation du rôle (gestion minuscules/majuscules)
        user_role = getattr(request.user, 'role', '')
        if user_role:
            user_role = str(user_role).lower()

        allowed = [role.lower() for role in self.allowed_roles]

        # 4. Vérification de la permission
        if user_role in allowed:
            return super().dispatch(request, *args, **kwargs)

        # 5. Si accès refusé : Message d'avertissement et redirection
        messages.error(request, f"Accès refusé. Votre rôle ({user_role}) n'a pas la permission d'accéder à cette page.")
        return redirect('home')  # Redirige vers la page d'accueil ou dashboard
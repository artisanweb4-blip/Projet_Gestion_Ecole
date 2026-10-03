from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect, render
from django_htmx.http import HttpResponseClientRedirect

from core.scoping import assign_school


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


class HtmxCrudMixin:
    """
    Rend une vue CRUD (Create / Update / Delete) compatible avec les modales HTMX :

    - Requête GET avec l'en-tête HX-Request  → renvoie uniquement le contenu
      de la modale (formulaire ou confirmation de suppression).
    - Requête POST avec HX-Request           → enregistre / supprime puis
      renvoie HX-Redirect (rechargement complet de la page + message).

    Sans HTMX (navigation classique), le comportement des pages complètes
    est préservé à l'identique.
    """

    # Template partiel affiché dans la modale (formulaire OU confirmation)
    partial_template = None
    # Titre affiché dans l'en-tête de la modale
    modal_title = ''
    # Message flash après un enregistrement / une suppression
    success_message = 'Enregistré avec succès.'
    # Mettre à False si la vue ajoute déjà elle-même son message
    add_success_message = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modal_title'] = self.modal_title
        context['modal_action'] = self.request.get_full_path()
        return context

    def _style_form(self, form):
        """Applique la classe form-control aux champs qui n'en ont pas."""
        for field in form.fields.values():
            current = field.widget.attrs.get('class', '')
            if 'form-control' not in current:
                field.widget.attrs['class'] = f'{current} form-control'.strip()

    def render_to_response(self, context, **response_kwargs):
        if self.request.htmx and self.partial_template:
            form = context.get('form')
            if form is not None:
                self._style_form(form)
            formset = context.get('formset')
            if formset is not None:
                for sub_form in formset.forms:
                    self._style_form(sub_form)
            return render(self.request, self.partial_template, context,
                          status=response_kwargs.get('status', 200))
        return super().render_to_response(context, **response_kwargs)

    def form_valid(self, form):
        # Isolation multi-écoles : rattache l'objet à l'école de l'utilisateur
        assign_school(form.instance, self.request.user)
        response = super().form_valid(form)
        if self.request.htmx:
            messages.success(self.request, self.success_message)
            return HttpResponseClientRedirect(str(self.get_success_url()))
        return response

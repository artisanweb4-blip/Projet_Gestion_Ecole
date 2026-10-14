from django.apps import apps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from core.mixins import HtmxCrudMixin, RoleRequiredMixin
from core.scoping import assign_school
from classes.models import Class
from parents.models import Parent

from .forms import StudentForm
from .models import Student


class StudentListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = Student
    template_name = 'students/list.html'
    context_object_name = 'students'
    allowed_roles = ['admin', 'director', 'secretary', 'teacher', 'superuser']
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('class_group')
        search = self.request.GET.get('search')
        class_filter = self.request.GET.get('class')
        status_filter = self.request.GET.get('status')

        if search:
            qs = qs.filter(
                first_name__icontains=search
            ) | qs.filter(
                last_name__icontains=search
            ) | qs.filter(
                student_id__icontains=search
            )

        if class_filter:
            qs = qs.filter(class_group__id=class_filter)

        if status_filter:
            qs = qs.filter(is_active=(status_filter == 'active'))

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ✅ Récupération dynamique du modèle Class sans import circulaire
        ClassModel = apps.get_model('classes', 'Class')
        
        context['classes'] = ClassModel.objects.all()
        context['search'] = self.request.GET.get('search', '')
        context['class_filter'] = self.request.GET.get('class', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class StudentParentLinkMixin:
    """Mixin partagé par la création et la modification d'élève :
    crée et lie le parent saisi directement dans le formulaire (inline)."""

    def form_valid(self, form):
        response = super().form_valid(form)
        self._link_inline_parent()
        return response

    def _link_inline_parent(self):
        """Crée et lie le parent saisi directement dans le formulaire élève."""
        first = (self.request.POST.get('parent_first_name') or '').strip()
        last = (self.request.POST.get('parent_last_name') or '').strip()
        if not first or not last:
            return

        try:
            email = (self.request.POST.get('parent_email') or '').strip().lower()
            parent = None
            if email:
                parent = Parent.objects.filter(email__iexact=email).first()
            if parent is None:
                parent = Parent.objects.filter(
                    first_name__iexact=first, last_name__iexact=last
                ).first()
            if parent is None:
                parent = Parent(
                    civility=self.request.POST.get('parent_civility') or 'M',
                    first_name=first, last_name=last, email=email or None,
                    phone=(self.request.POST.get('parent_phone') or '').strip() or None,
                    profession=(self.request.POST.get('parent_profession') or '').strip() or None,
                    address=(self.request.POST.get('parent_address') or '').strip() or None,
                )
                # Isolation multi-ecoles : le parent appartient a l'ecole de
                # l'utilisateur (sinon il est cree orphelin et invisible).
                assign_school(parent, self.request.user)
                try:
                    parent.save()
                except Exception:
                    # Email déjà utilisé ailleurs : on réessaie sans l'email
                    # plutôt que de faire échouer la création du parent.
                    parent.email = None
                    parent.save()
                messages.success(
                    self.request,
                    f"Parent « {parent} » créé et lié à {self.object.first_name} "
                    f"{self.object.last_name}."
                )
            else:
                messages.info(
                    self.request,
                    f"Parent existant « {parent} » lié à {self.object.first_name} "
                    f"{self.object.last_name}."
                )
            # Un parent orphe lie auparavant (ancien bug) est ratache a l'ecole
            # de l'utilisateur pour redevenir visible.
            if parent.school_id is None:
                assign_school(parent, self.request.user)
                parent.save()
            self.object.parents.add(parent)
        except Exception:
            # La creation du parent ne doit JAMAIS faire echouer
            # l'enregistrement de l'eleve.
            messages.warning(
                self.request,
                "L'élève est enregistré, mais la création du parent a échoué. "
                "Vous pouvez lier le parent depuis sa fiche."
            )


class StudentCreateView(StudentParentLinkMixin, LoginRequiredMixin, RoleRequiredMixin,
                        HtmxCrudMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/form.html'
    success_url = reverse_lazy('students:list')
    allowed_roles = ['admin', 'director', 'secretary']
    partial_template = 'students/student_form_modal.html'
    modal_title = 'Nouvel élève'
    success_message = 'Élève enregistré avec succès.'


class StudentUpdateView(StudentParentLinkMixin, LoginRequiredMixin, RoleRequiredMixin,
                        HtmxCrudMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/form.html'
    success_url = reverse_lazy('students:list')
    allowed_roles = ['admin', 'director', 'secretary']
    partial_template = 'students/student_form_modal.html'
    modal_title = "Modifier l'élève"
    success_message = 'Élève mis à jour.'


class StudentDeleteView(LoginRequiredMixin, RoleRequiredMixin, HtmxCrudMixin, DeleteView):
    model = Student
    success_url = reverse_lazy('students:list')
    allowed_roles = ['admin', 'director']
    template_name = 'students/confirm_delete.html'
    partial_template = 'includes/delete_modal.html'
    modal_title = 'Supprimer cet élève'
    success_message = 'Élève supprimé.'


class StudentDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    model = Student
    template_name = 'students/detail.html'
    context_object_name = 'student'
    allowed_roles = ['admin', 'director', 'secretary', 'teacher', 'parent']

@login_required
def export_students_excel(request):
    """Export Excel de la liste des élèves — par classe ou toutes classes.

    Colonnes identiques au modèle d'import : le fichier exporté peut être
    complété puis ré-importé dans Paramètres → Sauvegarde → Importer.
    """
    from django.http import HttpResponse
    from school_settings.excel_backup import build_xlsx

    school = getattr(request.user, 'school', None)
    qs = Student._base_manager.filter(school=school).select_related('class_group')

    class_id = request.GET.get('class')
    class_obj = None
    if class_id and class_id.isdigit():
        class_obj = Class.objects.filter(school=school, pk=int(class_id)).first()
        if class_obj:
            qs = qs.filter(class_group=class_obj)

    headers = ['Matricule', 'Prénom', 'Nom', 'Sexe', 'Date de naissance',
               'Lieu de naissance', 'Classe', 'Téléphone', 'Email',
               'Date inscription', 'Actif']

    def _row(s):
        return [
            s.student_id, s.first_name, s.last_name,
            s.get_gender_display() or '',
            s.date_of_birth.strftime('%d/%m/%Y') if s.date_of_birth else '',
            s.place_of_birth or '',
            s.class_group.name if s.class_group else '',
            s.phone or '', s.email or '',
            s.enrollment_date.strftime('%d/%m/%Y') if s.enrollment_date else '',
            'Oui' if s.is_active else 'Non',
        ]

    if class_obj:
        sheets = [(class_obj.name[:31], headers,
                   [_row(s) for s in qs.order_by('last_name', 'first_name')])]
        filename = f"eleves_{class_obj.name.replace(' ', '_')}.xlsx"
    else:
        sheets = []
        by_class = {}
        no_class = []
        for s in qs.order_by('class_group__name', 'last_name', 'first_name'):
            if s.class_group_id:
                by_class.setdefault(s.class_group.name, []).append(s)
            else:
                no_class.append(s)
        for name, students in sorted(by_class.items()):
            sheets.append((name[:31], headers, [_row(s) for s in students]))
        if no_class:
            sheets.append(('Sans classe', headers, [_row(s) for s in no_class]))
        if not sheets:
            sheets = [('Élèves', headers, [])]
        filename = 'eleves_toutes_classes.xlsx'

    content = build_xlsx(sheets)
    response = HttpResponse(
        content,
        content_type=(
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ),
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

from django.apps import apps
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


class StudentCreateView(LoginRequiredMixin, RoleRequiredMixin, HtmxCrudMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/form.html'
    success_url = reverse_lazy('students:list')
    allowed_roles = ['admin', 'director', 'secretary']
    partial_template = 'includes/form_modal.html'
    modal_title = 'Nouvel élève'
    success_message = 'Élève enregistré avec succès.'


class StudentUpdateView(LoginRequiredMixin, RoleRequiredMixin, HtmxCrudMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/form.html'
    success_url = reverse_lazy('students:list')
    allowed_roles = ['admin', 'director', 'secretary']
    partial_template = 'includes/form_modal.html'
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
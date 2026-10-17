# teachers/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from core.mixins import HtmxCrudMixin
from .forms import TeacherForm
from .models import Teacher


class TeacherListView(LoginRequiredMixin, ListView):
    model = Teacher
    template_name = 'teachers/teacher_list.html'
    context_object_name = 'teachers'


class TeacherCreateView(LoginRequiredMixin, HtmxCrudMixin, CreateView):
    model = Teacher
    form_class = TeacherForm
    template_name = 'teachers/teacher_form.html'
    success_url = reverse_lazy('teachers:list')
    partial_template = 'includes/form_modal.html'
    modal_title = 'Nouvel enseignant'
    success_message = 'Enseignant enregistré avec succès.'


class TeacherDetailView(LoginRequiredMixin, DetailView):
    model = Teacher
    template_name = 'teachers/teacher_detail.html'
    context_object_name = 'teacher'


class TeacherUpdateView(LoginRequiredMixin, HtmxCrudMixin, UpdateView):
    model = Teacher
    form_class = TeacherForm
    template_name = 'teachers/teacher_form.html'  # Même template que CreateView
    success_url = reverse_lazy('teachers:list')
    partial_template = 'includes/form_modal.html'
    modal_title = "Modifier l'enseignant"
    success_message = 'Enseignant mis à jour.'


class TeacherDeleteView(LoginRequiredMixin, HtmxCrudMixin, DeleteView):
    model = Teacher
    template_name = 'teachers/teacher_confirm_delete.html'
    success_url = reverse_lazy('teachers:list')
    partial_template = 'includes/delete_modal.html'
    modal_title = 'Supprimer cet enseignant'
    success_message = 'Enseignant supprimé.'

# parents/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from core.mixins import HtmxCrudMixin
from .forms import ParentForm
from .models import Parent


class ParentListView(LoginRequiredMixin, ListView):
    model = Parent
    template_name = 'parents/parent_list.html'
    context_object_name = 'parents'

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')

        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(email__icontains=query)
                | Q(phone__icontains=query)
                | Q(profession__icontains=query)
            )
        return queryset


class ParentCreateView(LoginRequiredMixin, HtmxCrudMixin, CreateView):
    model = Parent
    form_class = ParentForm
    template_name = 'parents/parent_form.html'
    success_url = reverse_lazy('parents:list')
    partial_template = 'includes/form_modal.html'
    modal_title = 'Nouveau parent'
    success_message = 'Parent enregistré avec succès.'


class ParentDetailView(LoginRequiredMixin, DetailView):
    model = Parent
    template_name = 'parents/parent_detail.html'
    context_object_name = 'parent'


class ParentUpdateView(LoginRequiredMixin, HtmxCrudMixin, UpdateView):
    model = Parent
    form_class = ParentForm
    template_name = 'parents/parent_form.html'
    success_url = reverse_lazy('parents:list')
    partial_template = 'includes/form_modal.html'
    modal_title = 'Modifier le parent'
    success_message = 'Parent mis à jour.'


class ParentDeleteView(LoginRequiredMixin, HtmxCrudMixin, DeleteView):
    model = Parent
    template_name = 'parents/parent_confirm_delete.html'
    success_url = reverse_lazy('parents:list')
    partial_template = 'includes/delete_modal.html'
    modal_title = 'Supprimer ce parent'
    success_message = 'Parent supprimé.'

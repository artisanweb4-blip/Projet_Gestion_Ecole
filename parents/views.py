# parents/views.py
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Parent

from django.views.generic import ListView
from django.db.models import Q
from .models import Parent

class ParentListView(ListView):
    model = Parent
    template_name = 'parents/parent_list.html'
    context_object_name = 'parents'

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        
        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query) |
                Q(phone__icontains=query) |
                Q(profession__icontains=query)
            )
        return queryset
class ParentCreateView(CreateView):
    model = Parent
    fields = ['civility', 'first_name', 'last_name', 'email', 'phone', 'profession', 'address']
    template_name = 'parents/parent_form.html'
    success_url = reverse_lazy('parents:list')

class ParentDetailView(DetailView):
    model = Parent
    template_name = 'parents/parent_detail.html'
    context_object_name = 'parent'

class ParentUpdateView(UpdateView):
    model = Parent
    fields = ['civility', 'first_name', 'last_name', 'email', 'phone', 'profession', 'address']
    template_name = 'parents/parent_form.html'
    success_url = reverse_lazy('parents:list')

class ParentDeleteView(DeleteView):
    model = Parent
    template_name = 'parents/parent_confirm_delete.html'
    success_url = reverse_lazy('parents:list')
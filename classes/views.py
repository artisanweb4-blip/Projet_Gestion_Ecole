# classes/views.py
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Class
from .forms import ClassForm  # Import de votre formulaire personnalisé


class ClassListView(ListView):
    model = Class
    template_name = 'classes/class_list.html'
    context_object_name = 'classes'
    
    def get_queryset(self):
        # Optimisation des requêtes SQL pour éviter les problèmes de performance (N+1 queries)
        return Class.objects.select_related('program', 'responsible').all()


class ClassCreateView(CreateView):
    model = Class
    form_class = ClassForm  # Utilisation du formulaire personnalisé avec le champ program
    template_name = 'classes/class_form.html'
    success_url = reverse_lazy('classes:list')


class ClassDetailView(DetailView):
    model = Class
    template_name = 'classes/class_detail.html'
    context_object_name = 'object'

    def get_queryset(self):
        return Class.objects.select_related('program', 'responsible')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # On passe directement la queryset d'élèves actifs au template
        context['students'] = self.object.students.filter(is_active=True)
        return context


class ClassUpdateView(UpdateView):
    model = Class
    form_class = ClassForm  # Utilisation du formulaire personnalisé pour la modification
    template_name = 'classes/class_form.html'
    success_url = reverse_lazy('classes:list')

    def get_queryset(self):
        return Class.objects.select_related('program', 'responsible')


class ClassDeleteView(DeleteView):
    model = Class
    template_name = 'classes/class_confirm_delete.html'
    success_url = reverse_lazy('classes:list')
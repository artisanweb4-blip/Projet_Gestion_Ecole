# classes/views.py
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from core.mixins import HtmxCrudMixin
from .models import Class
from .forms import ClassForm  # Import de votre formulaire personnalisé


class ClassListView(LoginRequiredMixin, ListView):
    model = Class
    template_name = 'classes/class_list.html'
    context_object_name = 'classes'
    
    def get_queryset(self):
        # Optimisation des requêtes SQL pour éviter les problèmes de performance (N+1 queries)
        return Class.objects.select_related('program', 'responsible').all()


class ClassCreateView(LoginRequiredMixin, HtmxCrudMixin, CreateView):
    model = Class
    form_class = ClassForm  # Utilisation du formulaire personnalisé avec le champ program
    template_name = 'classes/class_form.html'
    success_url = reverse_lazy('classes:list')
    partial_template = 'includes/form_modal.html'
    modal_title = 'Nouvelle classe'
    success_message = 'Classe enregistrée avec succès.'


class ClassDetailView(DetailView):
    model = Class
    template_name = 'classes/class_detail.html'
    context_object_name = 'object'

    def get_queryset(self):
        return Class.objects.select_related('program', 'responsible')

    def get_context_data(self, **kwargs):
        from accounting.views import student_finance_summary
        from django.db.models import Sum
        from finance.models import TuitionFee

        context = super().get_context_data(**kwargs)
        obj = self.object
        # On passe directement la queryset d'élèves actifs au template
        students = obj.students.filter(is_active=True).select_related('class_group')
        context['students'] = students

        # --- Situation des paiements de la classe (scolarité) ---
        tuition_rows = (TuitionFee.objects.filter(
            school=obj.school, level=obj.level, academic_year='2026-2027',
            is_active=True,
        ) if obj.school and obj.level else TuitionFee.objects.none())
        context['tuition_rows'] = tuition_rows
        expected_total = tuition_rows.aggregate(t=Sum('amount'))['t']

        rows, paid_total = [], 0
        for student in students:
            summary = student_finance_summary(student)
            paid_total += summary['paid']
            paid_f = float(summary['paid'])
            percent = (paid_f / float(expected_total) * 100) if expected_total else 0
            rows.append({
                'student': student,
                'expected': summary['expected'],
                'paid': summary['paid'],
                'reliquat': summary['reliquat'],
                'percent': min(round(percent, 1), 100),
            })

        expected_f = float(expected_total) if expected_total else 0
        class_percent = (float(paid_total) / expected_f * 100) if expected_f else 0
        context['finance'] = {
            'rows': rows,
            'class_expected': expected_total if expected_total is not None else 0,
            'class_paid': paid_total,
            'class_reliquat': (expected_total - paid_total) if expected_total is not None else None,
            'class_percent': min(round(class_percent, 1), 100),
        }
        return context


class ClassUpdateView(LoginRequiredMixin, HtmxCrudMixin, UpdateView):
    model = Class
    form_class = ClassForm  # Utilisation du formulaire personnalisé pour la modification
    template_name = 'classes/class_form.html'
    success_url = reverse_lazy('classes:list')

    def get_queryset(self):
        return Class.objects.select_related('program', 'responsible')

    partial_template = 'includes/form_modal.html'
    modal_title = 'Modifier la classe'
    success_message = 'Classe mise à jour.'


class ClassDeleteView(LoginRequiredMixin, HtmxCrudMixin, DeleteView):
    model = Class
    template_name = 'classes/class_confirm_delete.html'
    success_url = reverse_lazy('classes:list')
    partial_template = 'includes/delete_modal.html'
    modal_title = 'Supprimer cette classe'
    success_message = 'Classe supprimée.'
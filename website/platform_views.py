"""
Interface Super Admin : gestion globale de toutes les écoles.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    View,
)

from accounts.models import School, User
from classes.models import Class
from students.models import Student
from teachers.models import Teacher
from core.mixins import HtmxCrudMixin
from finance.models import StudentPayment

from .forms import PlatformSchoolForm


class SuperadminRequiredMixin(LoginRequiredMixin):
    """Accès réservé au super administrateur de la plateforme."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            messages.error(
                request,
                "Accès réservé au super administrateur de la plateforme."
            )
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)


class PlatformDashboardView(SuperadminRequiredMixin, TemplateView):
    """Vue globale : toutes les écoles, utilisateurs, statistiques."""
    template_name = 'website/platform_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        schools = School.objects.annotate(
            nb_users=Count('users', distinct=True),
        ).order_by('-created_at')

        query = self.request.GET.get('q')
        if query:
            from django.db.models import Q
            schools = schools.filter(
                Q(name__icontains=query) | Q(code__icontains=query)
                | Q(email__icontains=query)
            )

        role_counts = dict(
            User.objects.values_list('role').annotate(n=Count('id'))
        )

        context.update({
            'schools': schools,
            'nb_schools_total': School.objects.count(),
            'nb_schools_active': School.objects.filter(is_active=True).count(),
            'nb_users': User.objects.count(),
            'nb_students': Student.objects.filter(is_active=True).count(),
            'nb_teachers': Teacher.objects.filter(is_active=True).count(),
            'nb_classes': Class.objects.count(),
            'nb_admins': role_counts.get('ADMIN', 0),
            'nb_teachers_users': role_counts.get('TEACHER', 0),
            'nb_parents_users': role_counts.get('PARENT', 0),
            'nb_comptables': role_counts.get('COMPTABLE', 0),
            'total_payments': StudentPayment.objects.aggregate(
                t=Sum('amount_paid'))['t'] or 0,
            'q': query or '',
        })
        return context


class PlatformSchoolCreateView(SuperadminRequiredMixin, HtmxCrudMixin, CreateView):
    model = School
    form_class = PlatformSchoolForm
    template_name = 'website/platform_school_form.html'
    success_url = reverse_lazy('platform_dashboard')
    partial_template = 'includes/form_modal.html'
    modal_title = 'Nouvelle école'
    success_message = "École créée avec succès."

    def form_valid(self, form):
        response = super().form_valid(form)
        admin = User.objects.create_user(
            email=form.cleaned_data['admin_email'],
            username=form.cleaned_data['admin_email'].split('@')[0],
            password=form.cleaned_data['admin_password'],
            first_name=form.cleaned_data['admin_first_name'],
            last_name=form.cleaned_data['admin_last_name'],
            role='ADMIN',
        )
        admin.school = self.object
        admin.is_staff = True
        admin.save()
        messages.success(
            self.request,
            f"École « {self.object.name} » créée — administrateur : {admin.email}"
        )
        return response


class PlatformSchoolDetailView(SuperadminRequiredMixin, DetailView):
    model = School
    template_name = 'website/platform_school_detail.html'
    context_object_name = 'school'


class PlatformSchoolToggleView(SuperadminRequiredMixin, View):
    """Active / suspend une école."""

    def post(self, request, pk):
        school = get_object_or_404(School, pk=pk)
        school.is_active = not school.is_active
        school.save()
        state = "réactivée" if school.is_active else "suspendue"
        messages.success(request, f"École « {school.name} » {state}.")
        return redirect('platform_dashboard')


class PlatformSchoolDeleteView(SuperadminRequiredMixin, HtmxCrudMixin, DeleteView):
    model = School
    template_name = 'website/platform_school_delete.html'
    success_url = reverse_lazy('platform_dashboard')
    partial_template = 'includes/delete_modal.html'
    modal_title = 'Supprimer cette école'
    success_message = "École supprimée de la plateforme."


class PlatformUsersView(SuperadminRequiredMixin, ListView):
    """Tous les comptes utilisateurs de la plateforme."""
    template_name = 'website/platform_users.html'
    context_object_name = 'users'
    paginate_by = 25

    def get_queryset(self):
        qs = User.objects.select_related('school').order_by('-created_at')
        query = self.request.GET.get('q')
        role = self.request.GET.get('role')
        if query:
            from django.db.models import Q
            qs = qs.filter(
                Q(email__icontains=query) | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )
        if role:
            qs = qs.filter(role=role)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['roles'] = User.ROLE_CHOICES
        context['q'] = self.request.GET.get('q', '')
        context['f_role'] = self.request.GET.get('role', '')
        return context

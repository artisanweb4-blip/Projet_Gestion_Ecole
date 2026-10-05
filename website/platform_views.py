"""
Interface Super Admin : gestion globale de toutes les écoles.
"""
import uuid
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    FormView,
    TemplateView,
    UpdateView,
    View,
)

from accounts.models import PlatformSetting, School, SubscriptionPlan, User
from accounts.utils import unique_username
from analytics.models import VisitLog
from classes.models import Class
from students.models import Student
from teachers.models import Teacher
from core.mixins import HtmxCrudMixin
from finance.models import StudentPayment

from .forms import (
    PlatformSchoolForm,
    PlatformSchoolSubscriptionForm,
    PlatformSchoolUpdateForm,
    PlatformSettingsForm,
    PlatformSubscriptionForm,
    PlatformUserForm,
    PlatformUserPasswordForm,
)


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
    """Tableau de bord global de la plateforme (Super Admin)."""
    template_name = 'website/platform_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        d14 = today - timedelta(days=13)
        d30 = today - timedelta(days=29)
        month_start = today.replace(day=1)

        role_counts = dict(
            User.objects.values_list('role').annotate(n=Count('id'))
        )

        # --- Visites (analytique) ---
        visit_today = VisitLog.objects.filter(day=today).aggregate(
            users=Count('user', distinct=True), views=Count('id'))
        visit30 = VisitLog.objects.filter(day__gte=d30).aggregate(
            users=Count('user', distinct=True), views=Count('id'))

        # --- Activité des 14 derniers jours (barres CSS) ---
        daily_qs = (VisitLog.objects.filter(day__gte=d14)
                    .values('day')
                    .annotate(users=Count('user', distinct=True), views=Count('id'))
                    .order_by('day'))
        daily_map = {row['day']: row for row in daily_qs}
        visits_daily = []
        max_views = 1
        for i in range(14):
            day = d14 + timedelta(days=i)
            row = daily_map.get(day, {'users': 0, 'views': 0})
            max_views = max(max_views, row['views'])
            visits_daily.append({
                'label': day.strftime('%d/%m'),
                'users': row['users'], 'views': row['views'],
            })
        for row in visits_daily:
            row['pct'] = round(row['views'] * 100 / max_views)

        # --- Abonnements ---
        plan_stats = SubscriptionPlan.objects.annotate(
            nb=Count('schools', distinct=True)
        ).order_by('-nb')
        max_plan = max([p.nb for p in plan_stats] or [1])

        context.update({
            'nb_schools_total': School.objects.count(),
            'nb_schools_active': School.objects.filter(is_active=True).count(),
            'nb_schools_suspended': School.objects.filter(is_active=False).count(),
            'nb_schools_month': School.objects.filter(created_at__gte=month_start).count(),
            'nb_users': User.objects.count(),
            'nb_students': Student.objects.filter(is_active=True).count(),
            'nb_teachers': Teacher.objects.filter(is_active=True).count(),
            'nb_classes': Class.objects.count(),
            'nb_admins': role_counts.get('ADMIN', 0),
            'nb_parents_users': role_counts.get('PARENT', 0),
            'total_payments': StudentPayment.objects.aggregate(
                t=Sum('amount_paid'))['t'] or 0,
            'payments_month': StudentPayment.objects.filter(
                payment_date__gte=month_start).aggregate(
                t=Sum('amount_paid'))['t'] or 0,
            'visits_today_users': visit_today['users'] or 0,
            'visits_today_views': visit_today['views'] or 0,
            'visits30_users': visit30['users'] or 0,
            'visits30_views': visit30['views'] or 0,
            'visits_daily': visits_daily,
            'plan_stats': plan_stats,
            'plan_max': max_plan,
            'schools_without_plan': School.objects.filter(
                subscription__isnull=True).count(),
            'latest_schools': School.objects.select_related(
                'subscription').order_by('-created_at')[:5],
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
            username=unique_username(form.cleaned_data['admin_email']),
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        school = self.object
        context['nb_students'] = school.students.filter(is_active=True).count()
        context['nb_teachers'] = school.teachers.filter(is_active=True).count()
        context['nb_classes'] = school.classes.count()
        context['nb_parents'] = school.parents.count()
        context['school_users'] = school.users.select_related('school').order_by('role', 'email')
        return context


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


class PlatformSchoolUpdateView(SuperadminRequiredMixin, HtmxCrudMixin, UpdateView):
    """Modification d'une école (nom, formule, coordonnées)."""
    model = School
    form_class = PlatformSchoolUpdateForm
    template_name = 'website/platform_school_form.html'
    success_url = reverse_lazy('platform_dashboard')
    partial_template = 'includes/form_modal.html'
    modal_title = "Modifier l'école"
    success_message = "École mise à jour."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Modifier — {self.object.name}"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        return response


class PlatformUserCreateView(SuperadminRequiredMixin, HtmxCrudMixin, CreateView):
    """Création d'un compte utilisateur global (plateforme)."""
    model = User
    form_class = PlatformUserForm
    template_name = 'website/platform_user_form.html'
    success_url = reverse_lazy('platform_users')
    partial_template = 'includes/form_modal.html'
    modal_title = 'Nouvel utilisateur'
    success_message = "Utilisateur créé avec succès."

    def form_valid(self, form):
        form.instance.username = unique_username(form.cleaned_data['email'])
        form.instance.set_password(form.cleaned_data['password'])
        return super().form_valid(form)


class PlatformUserToggleView(SuperadminRequiredMixin, View):
    """Active / désactive un compte utilisateur."""

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user.pk == request.user.pk:
            messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
            return redirect('platform_users')
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        state = "activé" if user.is_active else "désactivé"
        messages.success(request, f"Compte « {user.email} » {state}.")
        return redirect('platform_users')


class PlatformUserPasswordView(SuperadminRequiredMixin, HtmxCrudMixin, FormView):
    """Réinitialisation du mot de passe d'un compte (modale + page complète)."""
    form_class = PlatformUserPasswordForm
    template_name = 'website/platform_user_password.html'
    success_url = reverse_lazy('platform_users')
    partial_template = 'includes/form_modal.html'
    modal_title = "Réinitialiser le mot de passe"
    success_message = "Mot de passe réinitialisé."

    def dispatch(self, request, *args, **kwargs):
        self.target_user = get_object_or_404(User, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['target_user'] = self.target_user
        return context

    def form_valid(self, form):
        self.target_user.set_password(form.cleaned_data['password'])
        self.target_user.save(update_fields=['password'])
        messages.success(
            self.request,
            f"Mot de passe de « {self.target_user.email} » réinitialisé."
        )
        if self.request.htmx:
            from django_htmx.http import HttpResponseClientRedirect
            return HttpResponseClientRedirect(str(self.get_success_url()))
        return redirect(self.get_success_url())


class PlatformUserDeleteView(SuperadminRequiredMixin, HtmxCrudMixin, DeleteView):
    """Suppression d'un compte utilisateur."""
    model = User
    template_name = 'website/platform_user_delete.html'
    success_url = reverse_lazy('platform_users')
    partial_template = 'includes/delete_modal.html'
    modal_title = 'Supprimer ce compte'
    success_message = "Compte supprimé."

    def form_valid(self, form):
        if self.object.pk == self.request.user.pk:
            messages.error(self.request, "Vous ne pouvez pas supprimer votre propre compte.")
            return redirect(self.get_success_url())
        if self.object.is_superuser and User.objects.filter(is_superuser=True).count() <= 1:
            messages.error(self.request, "Impossible de supprimer le dernier super administrateur.")
            return redirect(self.get_success_url())
        return super().form_valid(form)


class PlatformSchoolsView(SuperadminRequiredMixin, ListView):
    """Toutes les écoles du système — 20 par page, filtres et actions."""
    template_name = 'website/platform_schools.html'
    context_object_name = 'schools'
    paginate_by = 20

    def get_queryset(self):
        qs = School.objects.select_related('subscription').annotate(
            nb_users=Count('users', distinct=True),
            nb_students=Count('students', distinct=True),
            nb_teachers=Count('teachers', distinct=True),
            nb_classes=Count('classes', distinct=True),
        ).order_by('-created_at')

        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(
                Q(name__icontains=query) | Q(code__icontains=query)
                | Q(email__icontains=query) | Q(address__icontains=query)
            )
        status = self.request.GET.get('status')
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'suspended':
            qs = qs.filter(is_active=False)
        plan = self.request.GET.get('abonnement')
        if plan == 'none':
            qs = qs.filter(subscription__isnull=True)
        elif plan and plan.isdigit():
            qs = qs.filter(subscription_id=int(plan))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans'] = SubscriptionPlan.objects.order_by('price')
        context['q'] = self.request.GET.get('q', '')
        context['f_status'] = self.request.GET.get('status', '')
        context['f_abonnement'] = self.request.GET.get('abonnement', '')
        return context


class PlatformSchoolSubscriptionView(SuperadminRequiredMixin, HtmxCrudMixin, UpdateView):
    """Attribuer / modifier l'abonnement d'une école (modale + page)."""
    model = School
    form_class = PlatformSchoolSubscriptionForm
    template_name = 'website/platform_school_subscription.html'
    success_url = reverse_lazy('platform_schools')
    partial_template = 'includes/form_modal.html'
    modal_title = "Attribuer un abonnement"
    success_message = "Abonnement mis à jour."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Abonnement — {self.object.name}"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        sub = self.object.subscription
        if sub:
            until = self.object.subscription_until or (
                timezone.localdate() + timedelta(days=sub.duration_days))
            if self.object.subscription_until != until:
                self.object.subscription_until = until
                self.object.save(update_fields=['subscription_until'])
            messages.success(
                self.request,
                f"Abonnement « {sub.name} » attribué à « {self.object.name} » "
                f"(jusqu'au {self.object.subscription_until.strftime('%d/%m/%Y')})."
            )
        return response


class PlatformSubscriptionsView(SuperadminRequiredMixin, ListView):
    """Page Abonnements : toutes les formules proposées aux écoles."""
    template_name = 'website/platform_subscriptions.html'
    context_object_name = 'plans'

    def get_queryset(self):
        return SubscriptionPlan.objects.annotate(
            nb=Count('schools', distinct=True),
        ).order_by('-is_active', 'price')


class PlatformSubscriptionCreateView(SuperadminRequiredMixin, HtmxCrudMixin, CreateView):
    model = SubscriptionPlan
    form_class = PlatformSubscriptionForm
    template_name = 'website/platform_subscription_form.html'
    success_url = reverse_lazy('platform_subscriptions')
    partial_template = 'includes/form_modal.html'
    modal_title = 'Nouvel abonnement'
    success_message = "Abonnement créé."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Nouvel abonnement'
        return context

    def form_valid(self, form):
        if SubscriptionPlan.objects.filter(code=form.instance.code).exists():
            form.instance.code = f"{form.instance.code[:25]}-{str(uuid.uuid4())[:4]}"
        return super().form_valid(form)


class PlatformSubscriptionUpdateView(SuperadminRequiredMixin, HtmxCrudMixin, UpdateView):
    model = SubscriptionPlan
    form_class = PlatformSubscriptionForm
    template_name = 'website/platform_subscription_form.html'
    success_url = reverse_lazy('platform_subscriptions')
    partial_template = 'includes/form_modal.html'
    modal_title = "Modifier l'abonnement"
    success_message = "Abonnement mis à jour."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Modifier — {self.object.name}"
        return context


class PlatformSubscriptionDeleteView(SuperadminRequiredMixin, HtmxCrudMixin, DeleteView):
    model = SubscriptionPlan
    template_name = 'website/platform_subscription_delete.html'
    success_url = reverse_lazy('platform_subscriptions')
    partial_template = 'includes/delete_modal.html'
    modal_title = 'Supprimer cet abonnement'
    success_message = "Abonnement supprimé. Les écoles concernées n'en ont plus."


class PlatformAnalyticsView(SuperadminRequiredMixin, TemplateView):
    """Analytique : qui consulte la plateforme, par sexe et par région."""
    template_name = 'website/platform_analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        d14 = today - timedelta(days=13)
        d30 = today - timedelta(days=29)
        base = VisitLog.objects.filter(day__gte=d30)

        visit_today = VisitLog.objects.filter(day=today).aggregate(
            users=Count('user', distinct=True), views=Count('id'))

        def rows(field, label_map):
            data = (base.exclude(user=None)
                    .values(field)
                    .annotate(users=Count('user', distinct=True), views=Count('id'))
                    .order_by('-users'))
            items = [
                {'label': label_map.get(row[field]) or 'Non renseigné',
                 'users': row['users'], 'views': row['views']}
                for row in data
            ]
            total = sum(item['users'] for item in items) or 1
            for item in items:
                item['pct'] = round(item['users'] * 100 / total)
            return items

        gender_rows = rows('user__gender', dict(User.GENDER_CHOICES))
        region_rows = rows('user__region', dict(User.REGION_CHOICES))

        # Activité des 14 derniers jours (zéro rempli)
        daily_qs = (VisitLog.objects.filter(day__gte=d14)
                    .values('day')
                    .annotate(users=Count('user', distinct=True), views=Count('id'))
                    .order_by('day'))
        daily_map = {row['day']: row for row in daily_qs}
        daily = []
        max_views = 1
        for i in range(14):
            day = d14 + timedelta(days=i)
            row = daily_map.get(day, {'users': 0, 'views': 0})
            max_views = max(max_views, row['views'])
            daily.append({'label': day.strftime('%d/%m'),
                          'users': row['users'], 'views': row['views']})
        for row in daily:
            row['pct'] = round(row['views'] * 100 / max_views)

        top_pages = (base.values('path')
                     .annotate(views=Count('id'), users=Count('user', distinct=True))
                     .order_by('-views')[:8])
        by_school = (base.exclude(user__school=None)
                     .values('user__school__name')
                     .annotate(users=Count('user', distinct=True), views=Count('id'))
                     .order_by('-views')[:8])

        context.update({
            'visits_today_users': visit_today['users'] or 0,
            'visits_today_views': visit_today['views'] or 0,
            'unique_users_30': base.filter(user__isnull=False).aggregate(
                u=Count('user', distinct=True))['u'] or 0,
            'views_30': base.count(),
            'anonymous_30': base.filter(user__isnull=True).count(),
            'gender_rows': gender_rows,
            'region_rows': region_rows,
            'daily': daily,
            'top_pages': top_pages,
            'by_school': by_school,
        })
        return context


class PlatformSettingsView(SuperadminRequiredMixin, FormView):
    """Paramètres généraux de la plateforme."""
    template_name = 'website/platform_settings.html'
    form_class = PlatformSettingsForm
    success_url = reverse_lazy('platform_settings')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = PlatformSetting.load()
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Paramètres de la plateforme enregistrés.")
        return super().form_valid(form)

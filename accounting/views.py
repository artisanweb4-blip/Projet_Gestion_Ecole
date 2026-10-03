"""
Module Comptabilité : tableau de bord, frais scolaires et paiements.
Réservé aux rôles ADMIN et COMPTABLE.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Count, Sum
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from core.mixins import HtmxCrudMixin, RoleRequiredMixin
from finance.models import FeeStructure, StudentPayment

from .forms import FeeForm, PaymentForm

ALLOWED_ROLES = ['ADMIN', 'COMPTABLE']

METHOD_COLORS = {
    'CASH': '#059669',
    'ORANGE_MONEY': '#f97316',
    'WAVE': '#2563eb',
    'MTN_MOMO': '#facc15',
    'BANK_TRANSFER': '#7c3aed',
    'CHEQUE': '#64748b',
}


def _next_receipt_number():
    """Génère le prochain numéro de reçu (REC-<année>-<numéro>)."""
    year = timezone.now().year
    last = StudentPayment.objects.order_by('-id').first()
    n = last.id + 1 if last else 1
    return f"REC-{year}-{n:04d}"


class AccountingIndexView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    """Tableau de bord comptable : encaissements, répartition, activité."""
    template_name = 'accounting/index.html'
    allowed_roles = ALLOWED_ROLES

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        payments = StudentPayment.objects.select_related('student', 'fee_structure')
        total_all = payments.aggregate(t=Sum('amount_paid'))['t'] or 0
        count_all = payments.count()

        now = timezone.localtime()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        total_month = payments.filter(
            payment_date__gte=month_start
        ).aggregate(t=Sum('amount_paid'))['t'] or 0

        by_method = list(
            payments.values('payment_method')
            .annotate(total=Sum('amount_paid'), n=Count('id'))
            .order_by('-total')
        )
        max_method = max((m['total'] for m in by_method), default=0) or 1
        for row in by_method:
            row['label'] = row['payment_method']
            row['color'] = METHOD_COLORS.get(row['payment_method'], '#059669')
            row['percent'] = round(row['total'] * 100 / max_method)

        context.update({
            'total_all': total_all,
            'count_all': count_all,
            'total_month': total_month,
            'fees_count': FeeStructure.objects.count(),
            'by_method': by_method,
            'recent_payments': payments[:8],
        })
        return context


class FeeListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    template_name = 'accounting/fee_list.html'
    context_object_name = 'fees'
    allowed_roles = ALLOWED_ROLES

    def get_queryset(self):
        # IMPORTANT : évalué par requête (isolation multi-écoles)
        return (FeeStructure.objects.select_related('classroom')
                .order_by('-due_date'))


class FeeCreateView(LoginRequiredMixin, RoleRequiredMixin, HtmxCrudMixin, CreateView):
    allowed_roles = ALLOWED_ROLES
    model = FeeStructure
    form_class = FeeForm
    template_name = 'accounting/fee_form.html'
    success_url = reverse_lazy('accounting:fees')
    partial_template = 'includes/form_modal.html'
    modal_title = 'Nouveau frais scolaire'
    success_message = 'Frais enregistré avec succès.'

    def get_initial(self):
        return {'academic_year': f'{timezone.now().year}-{timezone.now().year + 1}'}


class FeeUpdateView(LoginRequiredMixin, RoleRequiredMixin, HtmxCrudMixin, UpdateView):
    allowed_roles = ALLOWED_ROLES
    model = FeeStructure
    form_class = FeeForm
    template_name = 'accounting/fee_form.html'
    success_url = reverse_lazy('accounting:fees')
    partial_template = 'includes/form_modal.html'
    modal_title = 'Modifier le frais'
    success_message = 'Frais mis à jour.'


class FeeDeleteView(LoginRequiredMixin, RoleRequiredMixin, HtmxCrudMixin, DeleteView):
    allowed_roles = ALLOWED_ROLES
    model = FeeStructure
    template_name = 'accounting/fee_confirm_delete.html'
    success_url = reverse_lazy('accounting:fees')
    partial_template = 'includes/delete_modal.html'
    modal_title = 'Supprimer ce frais'
    success_message = 'Frais supprimé.'


class PaymentListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    template_name = 'accounting/payment_list.html'
    context_object_name = 'payments'
    allowed_roles = ALLOWED_ROLES

    def get_queryset(self):
        return (
            StudentPayment.objects
            .select_related('student', 'fee_structure')
            .order_by('-payment_date')
        )


class PaymentCreateView(LoginRequiredMixin, RoleRequiredMixin, HtmxCrudMixin, CreateView):
    allowed_roles = ALLOWED_ROLES
    model = StudentPayment
    form_class = PaymentForm
    template_name = 'accounting/payment_form.html'
    success_url = reverse_lazy('accounting:payments')
    partial_template = 'includes/form_modal.html'
    modal_title = 'Enregistrer un paiement'
    success_message = 'Paiement enregistré avec succès.'

    def get_initial(self):
        initial = super().get_initial()
        initial['receipt_number'] = _next_receipt_number()
        return initial

    def form_valid(self, form):
        if not form.cleaned_data.get('receipt_number'):
            form.instance.receipt_number = _next_receipt_number()
        return super().form_valid(form)


class PaymentDeleteView(LoginRequiredMixin, RoleRequiredMixin, HtmxCrudMixin, DeleteView):
    allowed_roles = ALLOWED_ROLES
    model = StudentPayment
    template_name = 'accounting/payment_confirm_delete.html'
    success_url = reverse_lazy('accounting:payments')
    partial_template = 'includes/delete_modal.html'
    modal_title = 'Supprimer ce paiement'
    success_message = 'Paiement supprimé.'

    def form_valid(self, form):
        """Respecte la règle métier : reçu émis ⇒ suppression interdite."""
        self.object = self.get_object()
        try:
            self.object.delete()
        except ValidationError as exc:
            message = getattr(exc, 'message', None) or '; '.join(exc.messages)
            messages.error(self.request, message)
            return self._redirect()
        messages.success(self.request, self.success_message)
        return self._redirect()

    def _redirect(self):
        from django_htmx.http import HttpResponseClientRedirect
        if self.request.htmx:
            return HttpResponseClientRedirect(str(self.success_url))
        from django.shortcuts import redirect
        return redirect(str(self.success_url))

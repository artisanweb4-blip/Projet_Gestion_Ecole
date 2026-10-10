"""
Module Comptabilité : tableau de bord, frais par niveau, paiements
(individuel ou par classe, périodicité mois/trimestre/semestre/année),
reçus A5 et dépenses par catégorie. Réservé aux rôles ADMIN et COMPTABLE.
"""
import calendar
from datetime import date
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django_htmx.http import HttpResponseClientRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.db.models import Count, Sum
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)
from xhtml2pdf import pisa

from classes.models import Class
from core.mixins import HtmxCrudMixin, RoleRequiredMixin
from core.scoping import assign_school
from finance.models import Expense, StudentPayment, TuitionFee
from students.models import Student

from .forms import ExpenseForm, PaymentModeForm, TuitionFeeForm

ALLOWED_ROLES = ['ADMIN', 'COMPTABLE']

METHOD_COLORS = {
    'CASH': '#059669',
    'ORANGE_MONEY': '#f97316',
    'WAVE': '#2563eb',
    'MTN_MOMO': '#facc15',
    'BANK_TRANSFER': '#7c3aed',
    'CHEQUE': '#64748b',
}

CURRENT_YEAR = '2026-2027'


def _next_receipt_number():
    """Génère le prochain numéro de reçu (REC-<année>-<numéro>)."""
    year = timezone.now().year
    last = StudentPayment.objects.order_by('-id').first()
    n = last.id + 1 if last else 1
    return f"REC-{year}-{n:04d}"


def _default_period_label(periodicity):
    """Libellé de période par défaut selon la périodicité et la date du jour."""
    now = timezone.localtime()
    if periodicity == 'MOIS':
        return f"{calendar.month_name[now.month].capitalize()} {now.year}"
    if periodicity == 'TRIMESTRE':
        return f"Trimestre {((now.month - 1) // 3) + 1}"
    if periodicity == 'SEMESTRE':
        return f"Semestre {1 if now.month <= 6 else 2}"
    return f"Année {CURRENT_YEAR}"


def _tuition_amount(school, level, periodicity, academic_year=CURRENT_YEAR):
    """Montant du frais officiel pour un niveau et une périodicité (ou None)."""
    if not school or not level:
        return None
    fee = TuitionFee.objects.filter(
        school=school, level=level, periodicity=periodicity,
        academic_year=academic_year, is_active=True,
    ).first()
    return fee.amount if fee else None


def student_finance_summary(student, academic_year=CURRENT_YEAR):
    """Résumé financier d'un élève : attendu, payé, reliquat, statut."""
    school = student.school
    level = student.class_group.level if student.class_group else None
    fees = TuitionFee.objects.filter(
        school=school, level=level, academic_year=academic_year, is_active=True,
    ) if school and level else TuitionFee.objects.none()
    expected = fees.aggregate(t=Sum('amount'))['t']
    paid = StudentPayment.objects.filter(student=student).aggregate(
        t=Sum('amount_paid'))['t'] or 0
    expected = expected if expected is not None else None
    reliquat = (expected - paid) if expected is not None else None
    if expected is None:
        status = 'indefini'
    elif paid >= expected:
        status = 'solde'
    elif paid > 0:
        status = 'partiel'
    else:
        status = 'impaye'
    return {
        'expected': expected,
        'paid': paid,
        'reliquat': reliquat,
        'status': status,
    }


# ---------------------------------------------------------------------------
# Tableau de bord
# ---------------------------------------------------------------------------
class AccountingIndexView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    """Tableau de bord comptable : encaissements, dépenses, frais par niveau."""
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

        by_method = (
            payments.values('payment_method')
            .annotate(total=Sum('amount_paid'), n=Count('id'))
            .order_by('-total')
        )

        # --- Nouveaux indicateurs professionnels ---
        expenses_month = Expense.objects.filter(
            expense_date__gte=month_start.date()
        ).aggregate(t=Sum('amount'))['t'] or 0
        expenses_all = Expense.objects.aggregate(t=Sum('amount'))['t'] or 0
        tuitions_count = TuitionFee.objects.filter(
            academic_year=CURRENT_YEAR, is_active=True).count()
        balance_month = total_month - expenses_month
        month_label = f"{calendar.month_name[now.month].capitalize()} {now.year}"

        context.update({
            'total_all': total_all,
            'count_all': count_all,
            'total_month': total_month,
            'by_method': by_method,
            'method_colors': METHOD_COLORS,
            'expenses_month': expenses_month,
            'expenses_all': expenses_all,
            'balance_month': balance_month,
            'tuitions_count': tuitions_count,
            'month_label': month_label,
        })
        return context


# ---------------------------------------------------------------------------
# Frais de scolarité PAR NIVEAU (nouvelle grille officielle)
# ---------------------------------------------------------------------------
class TuitionListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    template_name = 'accounting/tuition_list.html'
    context_object_name = 'tuitions'
    allowed_roles = ALLOWED_ROLES

    def get_queryset(self):
        return TuitionFee.objects.order_by('level', 'periodicity')


class TuitionCreateView(LoginRequiredMixin, RoleRequiredMixin, HtmxCrudMixin, CreateView):
    allowed_roles = ALLOWED_ROLES
    model = TuitionFee
    form_class = TuitionFeeForm
    template_name = 'accounting/tuition_form.html'
    success_url = reverse_lazy('accounting:tuitions')
    partial_template = 'includes/form_modal.html'
    modal_title = 'Définir le frais de scolarité'
    success_message = 'Frais de scolarité enregistré pour ce niveau.'

    def form_valid(self, form):
        assign_school(form.instance, self.request.user)
        response = super().form_valid(form)
        if self.request.htmx:
            messages.success(self.request, self.success_message)
            return HttpResponseClientRedirect(str(self.get_success_url()))
        return response


class TuitionUpdateView(LoginRequiredMixin, RoleRequiredMixin, HtmxCrudMixin, UpdateView):
    allowed_roles = ALLOWED_ROLES
    model = TuitionFee
    form_class = TuitionFeeForm
    template_name = 'accounting/tuition_form.html'
    success_url = reverse_lazy('accounting:tuitions')
    partial_template = 'includes/form_modal.html'
    modal_title = 'Modifier le frais de scolarité'
    success_message = 'Frais de scolarité mis à jour.'


class TuitionDeleteView(LoginRequiredMixin, RoleRequiredMixin, HtmxCrudMixin, DeleteView):
    allowed_roles = ALLOWED_ROLES
    model = TuitionFee
    template_name = 'accounting/tuition_confirm_delete.html'
    success_url = reverse_lazy('accounting:tuitions')
    partial_template = 'includes/delete_modal.html'
    modal_title = 'Supprimer ce frais de scolarité'
    success_message = 'Frais de scolarité supprimé.'


# ---------------------------------------------------------------------------
# Paiements : par élève OU par classe, périodicité, reçu A5
# ---------------------------------------------------------------------------
class PaymentListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    template_name = 'accounting/payment_list.html'
    context_object_name = 'payments'
    allowed_roles = ALLOWED_ROLES

    def get_queryset(self):
        return (
            StudentPayment.objects
            .select_related('student', 'fee_structure', 'student__class_group')
            .order_by('-payment_date')
        )


class PaymentCreateView(LoginRequiredMixin, RoleRequiredMixin, HtmxCrudMixin, FormView):
    """Enregistrement d'un paiement : un élève ou toute la classe.

    - Mode « Un élève » : un reçu A5 est généré pour cet élève.
    - Mode « Toute la classe » : un paiement individuel (et son reçu) est
      créé pour chaque élève actif de la classe.
    Le montant suggéré provient de la grille des frais (niveau × périodicité).
    """
    allowed_roles = ALLOWED_ROLES
    form_class = PaymentModeForm
    template_name = 'accounting/payment_form.html'
    success_url = reverse_lazy('accounting:payments')
    partial_template = 'accounting/payment_form_modal.html'
    modal_title = 'Enregistrer un paiement'

    def get_initial(self):
        initial = super().get_initial()
        initial['periodicity'] = 'ANNUEL'
        initial['period_label'] = _default_period_label('ANNUEL')
        initial['payment_method'] = 'CASH'
        classroom_id = self.request.GET.get('classroom')
        if classroom_id:
            initial['classroom'] = classroom_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modal_title'] = self.modal_title
        context['modal_action'] = reverse('accounting:payment_add')
        context['current_year'] = CURRENT_YEAR
        return context

    def form_valid(self, form):
        mode = form.cleaned_data['mode']
        periodicity = form.cleaned_data['periodicity']
        period_label = (
            form.cleaned_data.get('period_label') or ''
        ).strip() or _default_period_label(periodicity)
        amount = form.cleaned_data['amount_paid']
        method = form.cleaned_data['payment_method']

        if mode == 'ELEVE':
            students = [form.cleaned_data['student']]
        else:
            students = list(
                form.cleaned_data['classroom'].students.filter(is_active=True)
            )

        created = []
        for student in students:
            payment = StudentPayment(
                student=student,
                school=student.school or self.request.user.school,
                periodicity=periodicity,
                period_label=period_label,
                amount_paid=amount,
                payment_method=method,
                receipt_number=_next_receipt_number(),
                is_receipt_issued=True,
            )
            payment.save()
            created.append(payment)

        if len(created) == 1:
            messages.success(
                self.request,
                f"Paiement enregistré — reçu n° {created[0].receipt_number}."
            )
        else:
            messages.success(
                self.request,
                f"{len(created)} paiement(s) enregistré(s) pour la classe "
                f"« {form.cleaned_data['classroom'].name} » (reçus individuels générés)."
            )
        if self.request.htmx:
            return HttpResponseClientRedirect(str(self.success_url))
        return redirect(self.success_url)

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        if self.request.htmx:
            return self.render_to_response(context)
        return self.render_to_response(context, status=400)

    def render_to_response(self, context, **response_kwargs):
        template = self.partial_template if self.request.htmx else self.template_name
        return render(self.request, template, context,
                      status=response_kwargs.get('status', 200))


class PaymentDeleteView(LoginRequiredMixin, RoleRequiredMixin, HtmxCrudMixin, DeleteView):
    allowed_roles = ALLOWED_ROLES
    model = StudentPayment
    template_name = 'accounting/payment_confirm_delete.html'
    success_url = reverse_lazy('accounting:payments')
    partial_template = 'includes/delete_modal.html'
    modal_title = 'Supprimer ce paiement'
    success_message = 'Paiement supprimé.'


class PaymentReceiptPDFView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    """Reçu de paiement au format A5 (PDF) : infos école, période, reliquat."""
    allowed_roles = ALLOWED_ROLES
    model = StudentPayment
    template_name = 'accounting/payment_receipt_pdf.html'

    def get(self, request, *args, **kwargs):
        payment = self.get_object()
        student = payment.student
        classroom = student.class_group
        school = payment.school or getattr(request.user, 'school', None)

        expected = _tuition_amount(school, classroom.level if classroom else None,
                                   payment.periodicity)
        paid_periodicity = StudentPayment.objects.filter(
            student=student, periodicity=payment.periodicity,
        ).aggregate(t=Sum('amount_paid'))['t'] or 0
        paid_total = StudentPayment.objects.filter(student=student).aggregate(
            t=Sum('amount_paid'))['t'] or 0
        reliquat = (expected - paid_periodicity) if expected is not None else None

        context = {
            'payment': payment,
            'student': student,
            'classroom': classroom,
            'school': school,
            'expected': expected,
            'paid_periodicity': paid_periodicity,
            'paid_total': paid_total,
            'reliquat': reliquat,
            'academic_year': CURRENT_YEAR,
            'now': timezone.localtime(),
        }
        html = render_to_string(self.template_name, context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode('UTF-8')), result, encoding='UTF-8')
        if pdf.err:
            return HttpResponse("Erreur lors de la génération du reçu.", status=500)
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        filename = f"recu_{payment.receipt_number}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response


class PaymentTuitionAjaxView(LoginRequiredMixin, RoleRequiredMixin, View):
    """Montant attendu (grille des frais) pour une classe et une périodicité."""

    allowed_roles = ALLOWED_ROLES

    def get(self, request, *args, **kwargs):
        class_id = request.GET.get('classroom')
        periodicity = request.GET.get('periodicity', 'ANNUEL')
        amount = None
        if class_id:
            classroom = Class.objects.filter(pk=class_id).first()
            amount = _tuition_amount(
                getattr(request.user, 'school', None),
                classroom.level if classroom else None,
                periodicity,
            )
        return JsonResponse({
            'amount': str(amount) if amount is not None else None,
            'hint': (
                f"{int(amount):,} FCFA attendus".replace(',', ' ')
                if amount is not None else
                "Aucun frais défini pour ce niveau/périodicité"
            ),
        })


# ---------------------------------------------------------------------------
# Dépenses par catégorie (filtrables par mois)
# ---------------------------------------------------------------------------
class ExpenseListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    template_name = 'accounting/expense_list.html'
    context_object_name = 'expenses'
    allowed_roles = ALLOWED_ROLES

    def get_queryset(self):
        qs = Expense.objects.order_by('-expense_date')
        month = self.request.GET.get('month')  # format YYYY-MM
        category = self.request.GET.get('category')
        if month:
            try:
                year, m = (int(x) for x in month.split('-'))
                qs = qs.filter(expense_date__year=year, expense_date__month=m)
            except (ValueError, TypeError):
                pass
        if category:
            qs = qs.filter(category=category)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Expense.CATEGORIES
        context['month'] = self.request.GET.get('month', '')
        context['category'] = self.request.GET.get('category', '')
        context['total'] = (self.get_queryset()
                            .aggregate(t=Sum('amount'))['t'] or 0)
        now = timezone.localtime()
        context['current_month'] = f"{now.year}-{now.month:02d}"
        return context


class ExpenseCreateView(LoginRequiredMixin, RoleRequiredMixin, HtmxCrudMixin, CreateView):
    allowed_roles = ALLOWED_ROLES
    model = Expense
    form_class = ExpenseForm
    template_name = 'accounting/expense_form.html'
    success_url = reverse_lazy('accounting:expenses')
    partial_template = 'includes/form_modal.html'
    modal_title = 'Nouvelle dépense'
    success_message = 'Dépense enregistrée.'

    def get_initial(self):
        initial = super().get_initial()
        initial['expense_date'] = timezone.localdate()
        return initial

    def form_valid(self, form):
        assign_school(form.instance, self.request.user)
        response = super().form_valid(form)
        if self.request.htmx:
            messages.success(self.request, self.success_message)
            return HttpResponseClientRedirect(str(self.get_success_url()))
        return response


class ExpenseUpdateView(LoginRequiredMixin, RoleRequiredMixin, HtmxCrudMixin, UpdateView):
    allowed_roles = ALLOWED_ROLES
    model = Expense
    form_class = ExpenseForm
    template_name = 'accounting/expense_form.html'
    success_url = reverse_lazy('accounting:expenses')
    partial_template = 'includes/form_modal.html'
    modal_title = 'Modifier la dépense'
    success_message = 'Dépense mise à jour.'


class ExpenseDeleteView(LoginRequiredMixin, RoleRequiredMixin, HtmxCrudMixin, DeleteView):
    allowed_roles = ALLOWED_ROLES
    model = Expense
    template_name = 'accounting/expense_confirm_delete.html'
    success_url = reverse_lazy('accounting:expenses')
    partial_template = 'includes/delete_modal.html'
    modal_title = 'Supprimer cette dépense'
    success_message = 'Dépense supprimée.'

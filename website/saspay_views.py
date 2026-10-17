"""
Paiement en ligne des abonnements via SasPay (côté école).

Flux (documentation https://docs.saspay.me) :

1. L'école clique « Payer en ligne » sur la page Mon abonnement.
   → création d'un paiement « En attente », puis appel
   ``POST /checkout-sessions/`` : SasPay renvoie un lien de paiement
   hébergé (checkout_url) sur lequel l'école choisit son réseau mobile
   money et confirme.
2. L'école revient sur ``/abonnement/saspay/retour/<id>/`` (return_url)
   → le statut réel est relu sur ``GET /checkout-sessions/{id}/status/``
   (jamais de confiance aveugle dans la redirection) :
   PAID → abonnement activé ; PENDING → à revérifier ;
   EXPIRED / CANCELLED → paiement marqué échoué.
3. En parallèle, SasPay peut notifier le webhook
   ``POST /api/v1/saspay/webhook/`` (signature HMAC vérifiée) qui confirme
   le paiement même si l'école a fermé son navigateur.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View

from accounts.models import SubscriptionPayment, SubscriptionPlan
from website import saspay


class SchoolAccessMixin(LoginRequiredMixin):
    """Résout l'école de l'utilisateur connecté (refus sinon)."""

    def dispatch(self, request, *args, **kwargs):
        self.school = getattr(request.user, 'school', None)
        if self.school is None:
            messages.error(request, "Seuls les comptes rattachés à une école "
                                    "peuvent payer un abonnement.")
            return redirect('subscription_page')
        return super().dispatch(request, *args, **kwargs)


def _start_checkout(request, payment, config):
    """Appelle SasPay, enregistre la session et renvoie l'URL de paiement."""
    session = saspay.create_checkout_session(payment, request, config)
    payment.provider_payment_id = (session.get('id') or '')[:100]
    payment.checkout_url = session.get('checkout_url') or ''
    payment.save(update_fields=['provider_payment_id', 'checkout_url'])
    return payment.checkout_url


class SubscriptionSasPayPayView(SchoolAccessMixin, View):
    """Lance un paiement SasPay pour une formule (POST depuis /abonnement/)."""

    def post(self, request, plan_pk):
        if not saspay.is_configured():
            messages.error(request, "Le paiement en ligne n'est pas activé. "
                                    "Contactez la plateforme.")
            return redirect('subscription_page')
        plan = get_object_or_404(SubscriptionPlan, pk=plan_pk, is_active=True)
        if not plan.price or plan.price <= 0:
            messages.info(request,
                          "La formule « %s » est gratuite : attribuez-la "
                          "directement depuis cette page." % plan.name)
            return redirect('subscription_page')

        payment = SubscriptionPayment.objects.create(
            school=self.school,
            plan=plan,
            amount=plan.price,
            source=SubscriptionPayment.SOURCE_API,
            status=SubscriptionPayment.STATUS_PENDING,
            provider='SASPAY',
            note=f"Paiement en ligne SasPay — {plan.name}",
        )
        config = saspay.get_config()
        try:
            checkout_url = _start_checkout(request, payment, config)
        except saspay.SasPayError as exc:
            payment.status = SubscriptionPayment.STATUS_FAILED
            payment.note = f"Paiement SasPay impossible : {exc}"[:200]
            payment.save(update_fields=['status', 'note'])
            messages.error(request, str(exc))
            return redirect('subscription_page')
        return redirect(checkout_url)


class SubscriptionSasPayReturnView(SchoolAccessMixin, View):
    """Retour de SasPay (ou vérification manuelle) d'un paiement.

    Relit le statut réel de la session chez SasPay avant tout effet :
    PAID → abonnement activé, PENDING → message d'attente,
    EXPIRED / CANCELLED → paiement échoué.
    """

    def get(self, request, pk):
        payment = get_object_or_404(
            SubscriptionPayment, pk=pk, school=self.school)
        if payment.status == SubscriptionPayment.STATUS_SUCCESS:
            messages.info(request, "Ce paiement a déjà été confirmé.")
            return redirect('subscription_page')
        if payment.status == SubscriptionPayment.STATUS_FAILED:
            messages.error(request, "Ce paiement a échoué : relancez-le.")
            return redirect('subscription_page')

        config = saspay.get_config()
        try:
            session = saspay.get_session_status(
                payment.provider_payment_id, config)
        except saspay.SasPayError as exc:
            messages.error(request, str(exc))
            return redirect('subscription_page')

        status = (session.get('status') or '').upper()
        transaction_status = (session.get('transaction_status') or '').upper()
        if status == 'PAID' or transaction_status == 'SUCCESS':
            saspay.confirm_payment(payment, session.get('msisdn') or '')
            plan_name = payment.plan.name if payment.plan else 'abonnement'
            messages.success(
                request,
                "Paiement confirmé, merci ! La formule « %s » est activée." % plan_name)
        elif status in ('EXPIRED', 'CANCELLED'):
            saspay.fail_payment(payment)
            messages.error(
                request,
                "La session de paiement a %s. Relancez un paiement."
                % ('expiré' if status == 'EXPIRED' else 'été annulée'))
        else:
            messages.warning(
                request,
                "Le paiement n'est pas encore confirmé par SasPay. "
                "Si vous venez de valider sur votre téléphone, réessayez "
                "dans quelques instants (bouton « Vérifier »).")
        return redirect('subscription_page')


class SasPayPaymentRetryView(SchoolAccessMixin, View):
    """Relance un paiement en attente ou échoué (nouvelle session SasPay)."""

    def post(self, request, pk):
        payment = get_object_or_404(
            SubscriptionPayment, pk=pk, school=self.school)
        if not saspay.is_configured():
            messages.error(request, "Le paiement en ligne n'est pas activé.")
            return redirect('subscription_page')
        if payment.status == SubscriptionPayment.STATUS_SUCCESS:
            messages.info(request, "Ce paiement est déjà confirmé.")
            return redirect('subscription_page')
        # Nouvelle tentative : paiement réinitialisé puis nouvelle session
        payment.status = SubscriptionPayment.STATUS_PENDING
        payment.provider_payment_id = ''
        payment.checkout_url = ''
        payment.save(update_fields=['status', 'provider_payment_id',
                                    'checkout_url'])
        config = saspay.get_config()
        try:
            checkout_url = _start_checkout(request, payment, config)
        except saspay.SasPayError as exc:
            payment.status = SubscriptionPayment.STATUS_FAILED
            payment.note = f"Paiement SasPay impossible : {exc}"[:200]
            payment.save(update_fields=['status', 'note'])
            messages.error(request, str(exc))
            return redirect('subscription_page')
        return redirect(checkout_url)

"""Endpoint API : enregistrer un paiement d'abonnement payé en ligne.

POST /api/v1/subscriptions/payments/
Authentification : JWT (/accounts/auth/login/) ou session.
Corps JSON : {"school": "<code ou nom>", "plan": "<code>",
              "amount": 150000 (optionnel), "reference": "..." (optionnel)}
"""
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import School, SubscriptionPayment, SubscriptionPlan


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_subscription_payment(request):
    """Enregistre un paiement d'abonnement effectué via l'API (Mobile Money...)."""
    school_ref = (request.data.get('school') or '').strip()
    plan_ref = (request.data.get('plan') or '').strip()
    if not school_ref:
        return Response({'error': "Le champ « school » est obligatoire."},
                        status=status.HTTP_400_BAD_REQUEST)

    school = School.objects.filter(code=school_ref).first() or \
        School.objects.filter(name__iexact=school_ref).first()
    if school is None:
        return Response({'error': f"École « {school_ref} » introuvable."},
                        status=status.HTTP_404_NOT_FOUND)

    plan = None
    if plan_ref:
        plan = SubscriptionPlan.objects.filter(code=plan_ref).first() or \
            SubscriptionPlan.objects.filter(name__iexact=plan_ref).first()
        if plan is None:
            return Response({'error': f"Formule « {plan_ref} » introuvable."},
                            status=status.HTTP_404_NOT_FOUND)

    amount = plan.price if plan else None
    raw_amount = request.data.get('amount')
    if raw_amount not in (None, ''):
        try:
            amount = round(float(raw_amount), 2)
        except (TypeError, ValueError):
            return Response({'error': "Montant invalide."},
                            status=status.HTTP_400_BAD_REQUEST)
    if not amount or amount <= 0:
        return Response({'error': "Aucun montant connu pour ce paiement."},
                        status=status.HTTP_400_BAD_REQUEST)

    payment = SubscriptionPayment.objects.create(
        school=school, plan=plan, amount=amount,
        source=SubscriptionPayment.SOURCE_API,
        reference=(request.data.get('reference') or '')[:100],
    )

    # Active l'abonnement de l'école pour la durée de la formule
    if plan:
        from datetime import timedelta
        from django.utils import timezone
        school.subscription = plan
        school.subscription_until = timezone.localdate() + timedelta(days=plan.duration_days)
        school.save(update_fields=['subscription', 'subscription_until'])

    return Response({
        'id': payment.pk,
        'school': school.name,
        'plan': plan.name if plan else None,
        'amount': float(payment.amount),
        'source': 'API',
        'reference': payment.reference,
        'subscription_until': school.subscription_until.isoformat() if school.subscription_until else None,
    }, status=status.HTTP_201_CREATED)


# --------------------------------------------------------------------------
# Webhook SasPay : notification temps réel des transactions.
# Sécurité (doc SasPay) : en-têtes X-Webhook-Signature / X-Webhook-Timestamp /
# X-Webhook-Event — HMAC-SHA256 du corps brut, âge ≤ 5 minutes.
# --------------------------------------------------------------------------
import json
from datetime import timedelta

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from website import saspay as saspay_client


def _match_payment(data, config):
    """Retrouve le paiement lié à une transaction SasPay.

    1. metadata.payment_id (posé à la création de la session de checkout) ;
    2. à défaut, les sessions SasPay « en attente » récentes dont le statut
       réel est déjà PAID — acceptée seulement si l'identifiant de
       transaction correspond, ou si une seule session est concernée.
    """
    metadata = data.get('metadata') if isinstance(data.get('metadata'), dict) else {}
    ref = metadata.get('payment_id')
    if ref:
        payment = SubscriptionPayment.objects.filter(
            pk=ref, provider='SASPAY').first()
        if payment:
            return payment
    txn_id = data.get('id') or ''
    candidates = list(SubscriptionPayment.objects.filter(
        provider='SASPAY',
        status=SubscriptionPayment.STATUS_PENDING,
        created_at__gte=timezone.now() - timedelta(days=7),
    ).exclude(provider_payment_id='').order_by('-created_at')[:20])
    paid = []
    for payment in candidates:
        try:
            session = saspay_client.get_session_status(
                payment.provider_payment_id, config)
        except saspay_client.SasPayError:
            continue
        if (session.get('status') or '').upper() != 'PAID':
            continue
        session_txn = session.get('transaction_id') or ''
        if txn_id and session_txn and session_txn == txn_id:
            return payment
        paid.append(payment)
    return paid[0] if (len(paid) == 1 and not txn_id) else None


@method_decorator(csrf_exempt, name='dispatch')
class SasPayWebhookView(View):
    """Récepteur du webhook SasPay (URL à déclarer dans le dashboard SasPay)."""

    def post(self, request):
        config = saspay_client.get_config()
        if not config.saspay_webhook_secret:
            return JsonResponse({'error': "Webhook SasPay non configuré."},
                                status=400)
        raw = request.body
        signature = request.headers.get('X-Webhook-Signature', '')
        timestamp = request.headers.get('X-Webhook-Timestamp', '')
        if not saspay_client.verify_webhook_signature(
                raw, signature, timestamp, config.saspay_webhook_secret):
            return JsonResponse({'error': "Signature de webhook invalide."},
                                status=401)
        try:
            payload = json.loads(raw.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'error': "Corps JSON illisible."}, status=400)

        event = payload.get('event') or request.headers.get('X-Webhook-Event', '')
        data = payload.get('data') or {}
        if event == 'webhook.test':
            return JsonResponse({'received': True, 'event': event})

        if event in ('transaction.success', 'transaction.failed',
                     'transaction.cancelled'):
            payment = _match_payment(data, config)
            if payment is None:
                # 200 : évite les relivraisons infinies d'un event non apparié
                return JsonResponse({'received': True, 'matched': False})
            if event == 'transaction.success':
                saspay_client.confirm_payment(
                    payment, (data.get('msisdn') or ''))
            else:
                saspay_client.fail_payment(payment)
            return JsonResponse({'received': True, 'matched': True})

        return JsonResponse({'received': True, 'event': event})

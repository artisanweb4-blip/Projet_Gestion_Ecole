"""Endpoint API : enregistrer un paiement d'abonnement payé en ligne.

POST /api/v1/subscriptions/payments/
Authentification : JWT (/accounts/auth/login/) ou session.
Corps JSON : {"school": "<code ou nom>", "plan": "<code>",
              "amount": 150000 (optionnel), "reference": "..." (optionnel)}
"""
from django.shortcuts import get_object_or_404

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

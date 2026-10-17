"""
Client de l'API SasPay (https://docs.saspay.me) — paiement mobile money.

Implémentation fidèle à la documentation SasPay (spécification OpenAPI,
https://docs.saspay.me/api-reference/openapi.json) :

- Base URL       : https://api.saspay.me/api/v1
- Authentification : ``Authorization: Bearer sk_test_...`` (test) ou
  ``sk_live_...`` (production), uniquement côté serveur.
- Enveloppe      : ``{"success": true, "data": {...}, "code": 200}`` ;
  en cas d'erreur ``{"success": false, "error": {"message": ..., "code": ...}}``.
  Certaines réponses (statut d'une session) arrivent sans enveloppe :
  le client gère les deux formats.
- Checkout hébergé : ``POST /checkout-sessions/`` — le client choisit son
  réseau et son numéro sur la page SasPay, puis revient via ``return_url``.
- Statut         : ``GET /checkout-sessions/{id}/status/`` →
  ``PENDING | PAID | EXPIRED | CANCELLED`` (+ ``transaction_id``,
  ``transaction_status``).
- Webhooks       : en-têtes ``X-Webhook-Signature`` (HMAC-SHA256 hex
  minuscule de ``"{timestamp}.{corps_brut}"`` avec le secret de signature),
  ``X-Webhook-Timestamp`` (secondes, tolérance 5 minutes) et
  ``X-Webhook-Event`` (ex. ``transaction.success``).

Seule la bibliothèque standard est utilisée (urllib) : aucun pip install.
"""
import hashlib
import hmac
import json
import time
import urllib.error
import urllib.request

from django.utils import timezone

from accounts.models import PlatformSetting, SubscriptionPayment

WEBHOOK_TOLERANCE_SECONDS = 300  # âge maximum d'un webhook (doc SasPay)


class SasPayError(Exception):
    """Erreur d'appel à l'API SasPay, avec message prêt à afficher."""


def get_config():
    """Configuration SasPay stockée dans les paramètres plateforme."""
    return PlatformSetting.load()


def is_configured(config=None):
    """Vrai si le paiement en ligne peut être utilisé."""
    cfg = config or get_config()
    return bool(cfg.saspay_enabled and cfg.saspay_secret_key)


def _format_amount(amount):
    """Montant au format attendu par l'API : chaîne « 5000.00 »."""
    return f"{amount:.2f}"


def saspay_request(method, path, config, payload=None):
    """Appel HTTP vers l'API SasPay avec gestion de l'enveloppe.

    Lève :class:`SasPayError` avec un message en français exploitable.
    """
    url = config.saspay_api_url.rstrip('/') + path
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    headers = {
        'Authorization': f'Bearer {config.saspay_secret_key}',
        'Accept': 'application/json',
    }
    if data is not None:
        headers['Content-Type'] = 'application/json'
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode('utf-8') or '{}')
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode('utf-8') or '{}')
        except Exception:
            body = {}
        if isinstance(body.get('error'), dict):
            raise SasPayError(body['error'].get('message') or
                              f"Erreur SasPay (HTTP {exc.code})") from exc
        if isinstance(body.get('error'), dict) is False and body.get('error'):
            raise SasPayError(f"Erreur SasPay (HTTP {exc.code}).") from exc
        # Erreur de validation : {"champ": ["message"]}
        first = None
        for key, value in body.items():
            if isinstance(value, (list, tuple)) and value:
                first = f"{key} : {value[0]}"
                break
        if first:
            raise SasPayError(f"Données refusées par SasPay — {first}") from exc
        raise SasPayError(f"Erreur SasPay (HTTP {exc.code}).") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise SasPayError(
            "Impossible de joindre SasPay. Vérifiez la connexion Internet "
            "du serveur, puis réessayez.") from exc
    except json.JSONDecodeError as exc:
        raise SasPayError("Réponse illisible de SasPay.") from exc

    if isinstance(body, dict) and 'success' in body:
        if not body.get('success'):
            error = body.get('error') or {}
            message = (error.get('message')
                       if isinstance(error, dict) else str(error)) or \
                      "Erreur SasPay inconnue."
            raise SasPayError(message)
        return body.get('data')
    return body  # réponse sans enveloppe (ex. statut d'une session)


def create_checkout_session(payment, request, config=None):
    """Crée une session de checkout hébergée pour un paiement en attente.

    Renvoie le dict SasPay (id, slug, checkout_url, status...).
    Le paiement est rattaché à la session via ``metadata.payment_id`` pour
    la réconciliation du webhook, et via ``return_url`` pour le retour du
    client.
    """
    cfg = config or get_config()
    if not is_configured(cfg):
        raise SasPayError(
            "Le paiement en ligne n'est pas configuré. Contactez la "
            "plateforme.")
    plan = payment.plan
    user = getattr(request, 'user', None)
    customer_name = (user.get_full_name() if user and user.is_authenticated
                     else '') or payment.school.name
    customer_email = (getattr(user, 'email', '') or payment.school.email or
                      'facturation@gestion-ecole.app')
    return_url = request.build_absolute_uri(
        f"/abonnement/saspay/retour/{payment.pk}/")
    payload = {
        'amount': _format_amount(payment.amount),
        'currency': cfg.saspay_currency,
        'country': cfg.saspay_country,
        'description': f"Abonnement {plan.name} — {payment.school.name}",
        'customer_name': customer_name,
        'customer_email': customer_email,
        'return_url': return_url,
        'metadata': {'payment_id': payment.pk, 'source': 'gestion-ecole'},
    }
    data = saspay_request('POST', '/checkout-sessions/', cfg, payload)
    if not isinstance(data, dict) or not data.get('checkout_url'):
        raise SasPayError("SasPay n'a pas renvoyé de lien de paiement.")
    return data


def get_session_status(session_id, config=None):
    """Statut d'une session de checkout : PENDING / PAID / EXPIRED / CANCELLED."""
    cfg = config or get_config()
    data = saspay_request('GET', f'/checkout-sessions/{session_id}/status/', cfg)
    if not isinstance(data, dict):
        raise SasPayError("Réponse inattendue de SasPay.")
    return data


def verify_webhook_signature(raw_body, signature, timestamp, secret):
    """Vérifie la signature HMAC-SHA256 d'un webhook (doc SasPay).

    Deux contrôles : l'âge de l'horodatage (± 5 minutes) puis la signature
    calculée sur le corps BRUT reçu : ``hmac(secret, "{ts}.{body}")``.
    """
    if not (raw_body and signature and timestamp and secret):
        return False
    try:
        ts = int(str(timestamp).strip())
    except (TypeError, ValueError):
        return False
    if abs(time.time() - ts) > WEBHOOK_TOLERANCE_SECONDS:
        return False
    signed = f"{ts}.".encode('utf-8') + raw_body
    expected = hmac.new(secret.encode('utf-8'), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, str(signature).strip().lower())


def confirm_payment(payment, msisdn=''):
    """Marque un paiement comme réussi et active l'abonnement (idempotent).

    L'abonnement court à partir d'aujourd'hui, ou est prolongé si
    l'abonnement actuel de l'école est encore valable plus longtemps.
    """
    if payment.status == SubscriptionPayment.STATUS_SUCCESS:
        return payment  # déjà confirmé
    payment.status = SubscriptionPayment.STATUS_SUCCESS
    if msisdn:
        payment.payer_msisdn = msisdn[:30]
    if payment.provider:
        payment.reference = payment.reference or payment.provider_payment_id or ''
    payment.save()

    school = payment.school
    plan = payment.plan
    if plan is not None:
        today = timezone.localdate()
        base = max(school.subscription_until or today, today)
        school.subscription = plan
        school.subscription_until = base + timezone.timedelta(days=plan.duration_days)
        school.save(update_fields=['subscription', 'subscription_until'])
    return payment


def fail_payment(payment):
    """Marque un paiement comme échoué (session expirée ou annulée)."""
    if payment.status == SubscriptionPayment.STATUS_SUCCESS:
        return payment
    payment.status = SubscriptionPayment.STATUS_FAILED
    payment.save(update_fields=['status'])
    return payment

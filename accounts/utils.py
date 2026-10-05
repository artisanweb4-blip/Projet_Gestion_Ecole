"""Utilitaires comptes : nom d'utilisateur unique (multi-écoles)."""
import uuid

from accounts.models import User


def unique_username(email):
    """Génère un username disponible à partir de l'email (jamais de collision)."""
    base = (email or '').split('@')[0].strip()[:140] or 'utilisateur'
    username = base
    while User.objects.filter(username__iexact=username).exists():
        username = f"{base[:130]}-{str(uuid.uuid4())[:5]}"
    return username

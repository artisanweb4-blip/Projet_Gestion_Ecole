"""Template tags & filtres utilitaires du projet."""
import decimal

from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()


@register.filter
def money(value):
    """Formate un montant avec séparateur de milliers + FCFA."""
    try:
        value = decimal.Decimal(value)
    except (decimal.InvalidOperation, TypeError, ValueError):
        return "0 FCFA"
    return f"{intcomma(value)} FCFA"

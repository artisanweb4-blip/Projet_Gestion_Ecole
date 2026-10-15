from django import template

register = template.Library()


@register.filter(name='fcfa')
def fcfa(value):
    """Montant professionnel : 155000 → « 155 000 » (espaces, sans décimales)."""
    try:
        n = float(value)
    except (TypeError, ValueError):
        return value
    return f"{n:,.0f}".replace(",", " ")

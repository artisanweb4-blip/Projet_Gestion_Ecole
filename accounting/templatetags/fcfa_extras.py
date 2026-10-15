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


@register.filter(name='sum_field')
def sum_field(queryset, field_name):
    """Somme d'un champ sur un queryset/liste (ex : student.payments.all|sum_field:"amount_paid")."""
    total = 0
    for obj in queryset or []:
        try:
            total += getattr(obj, field_name) or 0
        except Exception:
            pass
    return total


@register.filter(name='finance_summary')
def finance_summary(student):
    """Résumé financier d'un élève (attendu / payé / reliquat / statut)."""
    try:
        from accounting.views import student_finance_summary
        return student_finance_summary(student)
    except Exception:
        return None

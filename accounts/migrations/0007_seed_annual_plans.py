from django.db import migrations


PLANS = [
    {
        'code': 'essentiel',
        'name': 'Essentiel',
        'price': 75000,
        'duration_days': 365,
        'max_students': 150,
        'description': "Idéal pour démarrer la numérisation d'une petite école.",
        'features': (
            "Jusqu'à 150 élèves\n"
            "2 utilisateurs\n"
            "Élèves, parents & classes\n"
            "Emploi du temps & calendrier\n"
            "Tableau de bord de base\n"
            "Sauvegarde Excel\n"
            "- Support prioritaire"
        ),
    },
    {
        'code': 'pro',
        'name': 'Pro',
        'price': 150000,
        'duration_days': 365,
        'max_students': 500,
        'description': "La gestion complète : notes, bulletins et paiements.",
        'features': (
            "Jusqu'à 500 élèves\n"
            "5 utilisateurs\n"
            "Tout le plan Essentiel\n"
            "Notes, moyennes & bulletins Excel\n"
            "Paiements & reçus numérotés PDF\n"
            "Documents officiels (certificats, attestations)\n"
            "Comptabilité — dépenses & recettes\n"
            "Import / export Excel\n"
            "Support prioritaire"
        ),
    },
    {
        'code': 'excellence',
        'name': 'Excellence',
        'price': 300000,
        'duration_days': 365,
        'max_students': None,
        'description': "Pour les grands établissements, sans aucune limite.",
        'features': (
            "Élèves illimités\n"
            "Utilisateurs illimités\n"
            "Tout le plan Pro\n"
            "Analytique avancée & rapports détaillés\n"
            "Multi-années scolaires & archivage\n"
            "Formation à distance de l'équipe\n"
            "Support WhatsApp dédié"
        ),
    },
]


def seed_annual_plans(apps, schema_editor):
    """Crée (sans écraser) les 3 formules annuelles affichées sur la landing."""
    SubscriptionPlan = apps.get_model('accounts', 'SubscriptionPlan')
    for plan in PLANS:
        SubscriptionPlan.objects.get_or_create(code=plan['code'], defaults=plan)


def reverse_seed(apps, schema_editor):
    SubscriptionPlan = apps.get_model('accounts', 'SubscriptionPlan')
    SubscriptionPlan.objects.filter(code__in=[p['code'] for p in PLANS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_fix_orphan_fees'),
    ]

    operations = [
        migrations.RunPython(seed_annual_plans, reverse_seed),
    ]

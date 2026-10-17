from django.db import migrations


TRIAL = {
    'code': 'essai',
    'name': 'Essai gratuit',
    'price': 0,
    'duration_days': 15,
    'max_students': None,
    'description': "15 jours pour tester TOUTES les fonctionnalités, sans engagement.",
    'features': (
        "Toutes les fonctionnalités de l'application\n"
        "Élèves, parents & classes illimités\n"
        "Notes & bulletins Excel\n"
        "Paiements & reçus numérotés PDF\n"
        "Documents officiels (certificats, attestations)\n"
        "Comptabilité — dépenses & recettes\n"
        "Emploi du temps & calendrier\n"
        "Import / export Excel\n"
        "Support prioritaire"
    ),
    'is_active': True,
}


def seed_trial(apps, schema_editor):
    """Crée la formule d'essai (15 jours, tout inclus) et l'attribue par défaut."""
    SubscriptionPlan = apps.get_model('accounts', 'SubscriptionPlan')
    plan, _ = SubscriptionPlan.objects.get_or_create(code=TRIAL['code'], defaults=TRIAL)

    # Les nouvelles écoles démarrent avec la période d'essai de 15 jours.
    PlatformSetting = apps.get_model('accounts', 'PlatformSetting')
    for setting in PlatformSetting.objects.filter(default_plan__isnull=True):
        setting.default_plan = plan
        setting.save(update_fields=['default_plan'])


def reverse_seed(apps, schema_editor):
    SubscriptionPlan = apps.get_model('accounts', 'SubscriptionPlan')
    PlatformSetting = apps.get_model('accounts', 'PlatformSetting')
    trial = SubscriptionPlan.objects.filter(code='essai').first()
    if trial:
        PlatformSetting.objects.filter(default_plan=trial).update(default_plan=None)
        trial.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_seed_annual_plans'),
    ]

    operations = [
        migrations.RunPython(seed_trial, reverse_seed),
    ]

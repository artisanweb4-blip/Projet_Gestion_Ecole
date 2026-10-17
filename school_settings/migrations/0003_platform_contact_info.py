"""Contact de la plateforme : Boulkassoumbougou (Bamako), Mali.

Remplace les anciennes coordonnées de démonstration (Yaoundé, Cameroun)
par les coordonnées réelles. Chaque champ n'est modifié que s'il contient
encore l'ancienne valeur de démonstration — les valeurs personnalisées
par l'établissement ne sont jamais écrasées.
"""
from django.db import migrations

NEW_ADDRESS = 'Boulkassoumbougou, Bamako'
NEW_PHONE = '70 53 85 04 / 99 93 00 98'
NEW_EMAIL = 'contact@ecoleafricain.com'


def update_contact(apps, schema_editor):
    SchoolSetting = apps.get_model('school_settings', 'SchoolSetting')
    for setting in SchoolSetting.objects.all():
        changed = False
        if setting.address and 'Nkolbisson' in setting.address:
            setting.address = NEW_ADDRESS
            changed = True
        if setting.phone and '237' in setting.phone:
            setting.phone = NEW_PHONE
            changed = True
        if setting.email and 'cpbr-cm' in setting.email:
            setting.email = NEW_EMAIL
            changed = True
        if changed:
            setting.save()


def revert_contact(apps, schema_editor):
    SchoolSetting = apps.get_model('school_settings', 'SchoolSetting')
    for setting in SchoolSetting.objects.all():
        changed = False
        if setting.address == NEW_ADDRESS:
            setting.address = 'Quartier Nkolbisson, Yaoundé, Cameroun'
            changed = True
        if setting.phone == NEW_PHONE:
            setting.phone = '+237 6 99 12 34 56'
            changed = True
        if setting.email == NEW_EMAIL:
            setting.email = 'contact@cpbr-cm.edu'
            changed = True
        if changed:
            setting.save()


class Migration(migrations.Migration):

    dependencies = [
        ('school_settings', '0002_schoolsetting_school'),
    ]

    operations = [
        migrations.RunPython(update_contact, revert_contact),
    ]

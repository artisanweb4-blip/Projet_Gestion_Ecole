"""
Rattache les frais scolaires sans classe (données antérieures au
multi-écoles) à la première classe de l'école principale, afin qu'ils
redeviennent visibles et modifiables par l'administration de l'école.
Ne fait rien si l'installation compte plusieurs écoles (cas ambigu).
"""
from django.db import migrations


def fix_orphans(apps, schema_editor):
    School = apps.get_model('accounts', 'School')
    Class = apps.get_model('classes', 'Class')
    FeeStructure = apps.get_model('finance', 'FeeStructure')

    if School.objects.count() != 1:
        return
    school = School.objects.first()
    classroom = Class.objects.filter(school=school).order_by('id').first()
    if classroom is None:
        return
    FeeStructure.objects.filter(classroom__isnull=True).update(classroom=classroom)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_subscriptionplan_school_subscription_until_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_orphans, migrations.RunPython.noop),
    ]

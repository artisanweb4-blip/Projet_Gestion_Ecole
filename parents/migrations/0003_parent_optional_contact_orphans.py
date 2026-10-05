"""Email/téléphone du parent facultatifs + rattrapage des parents orphelins.

Les parents créés depuis le formulaire élève pouvaient être enregistrés
sans école (orphelins, invisibles) ou sans email/téléphone (échec
d'enregistrement). Cette migration :
1. rend email et téléphone facultatifs en base ;
2. rattache les parents orphelins à la première école existante.
"""
from django.db import migrations, models


def attach_orphans(apps, schema_editor):
    Parent = apps.get_model('parents', 'Parent')
    School = apps.get_model('accounts', 'School')
    school = School.objects.order_by('id').first()
    if school is None:
        return
    Parent.objects.filter(school__isnull=True).update(school=school)


def unattach(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('parents', '0002_parent_school'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parent',
            name='email',
            field=models.EmailField(blank=True, null=True, unique=True, verbose_name='Email'),
        ),
        migrations.AlterField(
            model_name='parent',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Téléphone'),
        ),
        migrations.RunPython(attach_orphans, unattach),
    ]

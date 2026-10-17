"""Frais de scolarité par niveau, dépenses par catégorie, paiements périodisés."""
from django.db import migrations, models
import django.db.models.deletion


def backfill_schools(apps, schema_editor):
    """Rattache chaque paiement à l'école de son élève."""
    StudentPayment = apps.get_model('finance', 'StudentPayment')
    for p in StudentPayment.objects.filter(school__isnull=True).select_related('student'):
        if p.student.school_id:
            p.school_id = p.student.school_id
            p.save(update_fields=['school'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TuitionFee',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('level', models.CharField(choices=[('1ère', '1ère année'), ('2ème', '2ème année'), ('3ème', '3ème année'), ('4ème', '4ème année'), ('5ème', '5ème année'), ('6ème', '6ème année'), ('7ème', '7ème année'), ('8ème', '8ème année'), ('9ème', '9ème année'), ('10ème', '10ème Année (Seconde)'), ('11ème', '11ème Année (Première)'), ('12ème', '12ème Année (Terminal)'), ('Seconde', 'Seconde'), ('Première', 'Première'), ('Terminale', 'Terminale'), ('L1', 'Licence 1'), ('L2', 'Licence 2'), ('L3', 'Licence 3'), ('M1', 'Master 1'), ('M2', 'Master 2'), ('Doctorat', 'Doctorat')], max_length=20, verbose_name='Niveau de classe')),
                ('periodicity', models.CharField(choices=[('MOIS', 'Par mois'), ('TRIMESTRE', 'Par trimestre'), ('SEMESTRE', 'Par semestre'), ('ANNUEL', 'Par année')], default='ANNUEL', max_length=12, verbose_name='Périodicité')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Montant (FCFA)')),
                ('academic_year', models.CharField(default='2026-2027', max_length=20, verbose_name='Année académique')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('school', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tuition_fees', to='accounts.school', verbose_name='École')),
            ],
            options={
                'verbose_name': 'Frais de scolarité (par niveau)',
                'verbose_name_plural': 'Frais de scolarité (par niveau)',
                'ordering': ['level', 'periodicity'],
            },
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.CharField(choices=[('SALAIRES', 'Salaires & personnel'), ('FOURNITURES', 'Fournitures & équipements'), ('MAINTENANCE', 'Maintenance & réparations'), ('UTILITES', 'Eau & électricité'), ('TRANSPORT', 'Transport'), ('COMMUNICATION', 'Communication & internet'), ('LOCATION', 'Loyer'), ('EVENEMENT', 'Événements & cérémonies'), ('AUTRE', 'Autres')], default='AUTRE', max_length=20, verbose_name='Catégorie')),
                ('label', models.CharField(max_length=150, verbose_name='Libellé de la dépense')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Montant (FCFA)')),
                ('expense_date', models.DateField(verbose_name='Date de la dépense')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('school', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='expenses', to='accounts.school', verbose_name='École')),
            ],
            options={
                'verbose_name': 'Dépense',
                'verbose_name_plural': 'Dépenses',
                'ordering': ['-expense_date'],
            },
        ),
        migrations.AddField(
            model_name='studentpayment',
            name='periodicity',
            field=models.CharField(choices=[('MOIS', 'Par mois'), ('TRIMESTRE', 'Par trimestre'), ('SEMESTRE', 'Par semestre'), ('ANNUEL', 'Par année')], default='ANNUEL', max_length=12, verbose_name='Périodicité du paiement'),
        ),
        migrations.AddField(
            model_name='studentpayment',
            name='period_label',
            field=models.CharField(blank=True, default='', max_length=60, verbose_name='Période concernée (ex : Octobre 2026, Trimestre 1)'),
        ),
        migrations.AddField(
            model_name='studentpayment',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='accounts.school', verbose_name='École'),
        ),
        migrations.AlterUniqueTogether(
            name='tuitionfee',
            unique_together={('school', 'level', 'periodicity', 'academic_year')},
        ),
        migrations.RunPython(backfill_schools, noop),
    ]

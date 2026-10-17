"""Retrait des tranches & échéances (FeeStructure) au profit de la grille par niveau."""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0003_expense_is_active_alter_expense_created_at_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentpayment',
            name='fee_structure',
        ),
        migrations.DeleteModel(
            name='FeeStructure',
        ),
    ]

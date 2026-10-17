"""Supprime TOUTES les données de démonstration du système.

Conserve : écoles, comptes utilisateurs, abonnements (catalogue),
paramètres. Supprime : élèves, parents, professeurs, classes, matières,
programmes, notes, évaluations, frais, paiements, emploi du temps,
salles, calendrier, documents, devoirs, examens, candidatures…
"""
from django.apps import apps
from django.core.management.base import BaseCommand

# Modèles conservés (structure du système, pas des données de démo)
KEEP = {
    'User', 'Group', 'Permission', 'School', 'SubscriptionPlan',
    'GeneralSetting', 'SchoolSetting', 'NotificationSetting',
    'BackupSetting', 'Session', 'LogEntry', 'ContentType',
}


class Command(BaseCommand):
    help = "Supprime les données de démonstration (élèves, notes, frais, etc.)"

    def handle(self, *args, **options):
        deleted_total = 0
        # Deux passes : la seconde nettoie les relations restantes
        for pass_num in (1, 2):
            for model in apps.get_models():
                if model._meta.auto_created or model._meta.abstract:
                    continue
                if model.__name__ in KEEP:
                    continue
                if model._meta.app_label in ('admin', 'sessions', 'contenttypes', 'auth'):
                    continue
                count, _ = model._base_manager.all().delete()
                deleted_total += count
        self.stdout.write(self.style.SUCCESS(
            f"{deleted_total} enregistrement(s) de démonstration supprimé(s)."
        ))
        self.stdout.write("Conservés : écoles, utilisateurs, paramètres, abonnements.")

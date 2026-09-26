from django.db import models

class TimeStampMixin(models.Model):
    """
    Classe abstraite fournissant l'horodatage automatique 'created_at' et 'updated_at'
    pour tous les modèles du projet (Exigence des spécifications).
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        abstract = True

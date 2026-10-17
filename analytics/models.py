"""Suivi des consultations de la plateforme (analytique Super Admin)."""
from django.conf import settings
from django.db import models
from django.db.models import Q


class VisitLog(models.Model):
    """Une consultation (utilisateur + jour + page), dédupliquée par jour.

    Permet l'analytique par sexe et par région (profil de l'utilisateur).
    Les visiteurs non identifiés sont comptés via la clé de session.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='visits',
        verbose_name="Visiteur",
    )
    session_key = models.CharField(max_length=40, blank=True, default='')
    path = models.CharField(max_length=200, verbose_name="Page")
    day = models.DateField(verbose_name="Jour", db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=250, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Visite"
        verbose_name_plural = "Visites"
        ordering = ['-day', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'day', 'path'], name='uniq_visit_user_day_path'
            ),
            models.UniqueConstraint(
                fields=['session_key', 'day', 'path'],
                condition=Q(user__isnull=True),
                name='uniq_visit_session_day_path',
            ),
        ]
        indexes = [models.Index(fields=['day', 'path'])]

    def __str__(self):
        who = self.user.email if self.user_id else self.session_key or 'anonyme'
        return f"{who} · {self.path} · {self.day}"

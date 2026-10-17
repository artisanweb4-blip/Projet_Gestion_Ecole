from django.db import models


class ContactMessage(models.Model):
    """Message envoyé depuis le formulaire de contact de la page d'accueil."""
    SUBJECTS = (
        ('INFO', "Demande d'information"),
        ('SUPPORT', 'Assistance technique'),
        ('PARTENARIAT', 'Partenariat'),
        ('INSCRIPTION', "Inscription d'une école"),
        ('AUTRE', 'Autre'),
    )

    name = models.CharField(max_length=120, verbose_name="Nom complet")
    email = models.EmailField(verbose_name="Adresse email")
    phone = models.CharField(max_length=30, blank=True, default='', verbose_name="Téléphone")
    subject = models.CharField(max_length=20, choices=SUBJECTS, default='INFO', verbose_name="Sujet")
    message = models.TextField(verbose_name="Message")
    is_handled = models.BooleanField(default=False, verbose_name="Traité")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Message de contact"
        verbose_name_plural = "Messages de contact"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} — {self.get_subject_display()}"

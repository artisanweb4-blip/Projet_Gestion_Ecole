from django.db import models

from core.scoping import SchoolManager, scoped_manager
from core.models import TimeStampMixin
from classes.models import Class as ClassRoom

class AdmissionApplication(TimeStampMixin):
    """Candidature / Demande d'admission d'un nouvel élève."""
    objects = SchoolManager()

    school = models.ForeignKey(
        'accounts.School',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='admissions',
        verbose_name="École",
    )
    STATUS_CHOICES = (
        ('PENDING', 'En attente d\'examen'),
        ('INTERVIEW', 'Entretien programmé'),
        ('APPROVED', 'Admission Approuvée'),
        ('REJECTED', 'Candidature Refusée'),
    )

    application_number = models.CharField(max_length=50, unique=True, verbose_name="Numéro de Dossier")
    applicant_first_name = models.CharField(max_length=150, verbose_name="Prénom du candidat")
    applicant_last_name = models.CharField(max_length=150, verbose_name="Nom du candidat")
    applicant_email = models.EmailField(verbose_name="Email de contact")
    applicant_phone = models.CharField(max_length=30, verbose_name="Téléphone de contact")
    requested_classroom = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True, blank=True, related_name='admissions', verbose_name="Niveau / Classe visée")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Statut du dossier")
    documents = models.FileField(upload_to='admissions/', blank=True, null=True, verbose_name="Dossier scolaire antérieur (PDF)")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes de la commission d'admission")

    class Meta:
        verbose_name = "Demande d'admission"
        verbose_name_plural = "Demandes d'admission"
        constraints = [
            models.UniqueConstraint(fields=['application_number'], name='unique_admission_app_number')
        ]

    def __str__(self):
        return f"[{self.application_number}] {self.applicant_first_name} {self.applicant_last_name} ({self.get_status_display()})"

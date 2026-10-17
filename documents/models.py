from django.db import models

from core.scoping import SchoolManager, scoped_manager
from django.conf import settings

class DocumentCategorie(models.TextChoices):
    CERTIFICAT = 'CERTIFICAT', 'Certificats & Attestations'
    PEDAGOGIQUE = 'PEDAGOGIQUE', 'Documents Pédagogiques & Classes'
    RH = 'RH', 'Documents du Personnel / RH'
    ADMINISTRATIF = 'ADMINISTRATIF', 'Documents Administratifs & Généraux'

class DocumentType(models.TextChoices):
    PDF = 'PDF', 'Document PDF'
    WORD = 'WORD', 'Document Word (.docx)'
    EXCEL = 'EXCEL', 'Feuille Excel (.xlsx)'

class DocumentModele(models.Model):
    """
    Modèles de documents téléchargeables ou consultables 
    (ex: Règlement intérieur, Modèle de contrat, Calendrier)
    """
    objects = SchoolManager()

    school = models.ForeignKey(
        'accounts.School',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_modeles',
        verbose_name="École",
    )
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    categorie = models.CharField(max_length=50, choices=DocumentCategorie.choices)
    type_fichier = models.CharField(max_length=10, choices=DocumentType.choices, default=DocumentType.PDF)
    fichier = models.FileField(upload_to='documents/modeles/')
    est_actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Modèle de document"
        verbose_name_plural = "Modèles de documents"

    def __str__(self):
        return self.titre


class DemandeConge(models.Model):
    """
    Demandes de congé et d'autorisation d'absence du personnel
    """
    objects = scoped_manager('employe__school')

    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('APPROUVE', 'Approuvé'),
        ('REFUSE', 'Refusé'),
    ]

    employe = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='demandes_conge')
    type_conge = models.CharField(max_length=100, choices=[
        ('ANNUEL', 'Congé annuel'),
        ('MALADIE', 'Congé maladie'),
        ('MATERNITE', 'Congé de maternité / paternité'),
        ('SANS_SOLDE', 'Autorisation d\'absence sans solde'),
        ('AUTRE', 'Autre'),
    ])
    date_debut = models.DateField()
    date_fin = models.DateField()
    motif = models.TextField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Demande de congé"
        verbose_name_plural = "Demandes de congé"

    def __str__(self):
        return f"Demande de congé - {self.employe} ({self.date_debut} au {self.date_fin})"
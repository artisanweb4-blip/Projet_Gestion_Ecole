from django.db import models
from django.core.exceptions import ValidationError
from core.models import TimeStampMixin
from students.models import ClassRoom, StudentProfile

class FeeStructure(TimeStampMixin):
    """Structure tarifaire et échéances des frais de scolarité."""
    name = models.CharField(max_length=150, verbose_name="Libellé du frais (ex: Tranche 1 Scolarité)")
    classroom = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True, blank=True, related_name='fee_structures', verbose_name="Classe ciblée")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant requis (FCFA / EUR)")
    due_date = models.DateField(verbose_name="Date limite d'échéance")
    academic_year = models.CharField(max_length=20, default="2025-2026", verbose_name="Année Académique")

    class Meta:
        verbose_name = "Structure de Frais"
        verbose_name_plural = "Structures de Frais"

    def __str__(self):
        cls_str = self.classroom.name if self.classroom else "Toutes classes"
        return f"{self.name} - {cls_str} ({self.amount} FCFA)"


class StudentPayment(TimeStampMixin):
    """
    Enregistrement de règlement / paiement effectué par un étudiant.
    Intègre le verrouillage strict si un reçu officiel a été émis.
    """
    PAYMENT_METHODS = (
        ('CASH', 'Espèces (Caisse)'),
        ('BANK_TRANSFER', 'Virement BTP / Banque'),
        ('ORANGE_MONEY', 'Orange Money'),
        ('WAVE', 'Wave Mobile Money'),
        ('MTN_MOMO', 'MTN Mobile Money'),
        ('CHEQUE', 'Chèque bancaire'),
    )

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='payments', verbose_name="Étudiant")
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments', verbose_name="Frais rattaché")
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant réglé")
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name="Date de versement")
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHODS, default='ORANGE_MONEY', verbose_name="Mode de paiement")
    receipt_number = models.CharField(max_length=100, unique=True, verbose_name="Numéro de reçu officiel")
    is_receipt_issued = models.BooleanField(default=True, verbose_name="Reçu officiel validé et émis")

    class Meta:
        verbose_name = "Paiement Étudiant"
        verbose_name_plural = "Paiements Étudiants"
        constraints = [
            models.UniqueConstraint(fields=['receipt_number'], name='unique_receipt_number')
        ]

    def delete(self, *args, **kwargs):
        """Règle Métier 4 : Un paiement ne peut pas être supprimé si le reçu a déjà été émis."""
        if self.is_receipt_issued:
            raise ValidationError("Impédance Sécurité : Impossible de supprimer un paiement dont le reçu officiel a déjà été émis.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Reçu #{self.receipt_number} - {self.student.user.get_full_name()} : {self.amount_paid} FCFA"

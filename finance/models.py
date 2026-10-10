from django.db import models

from core.scoping import SchoolManager, scoped_manager
from django.core.exceptions import ValidationError
from core.models import TimeStampMixin
from classes.models import Class as ClassRoom
from students.models import Student as StudentProfile

class FeeStructure(TimeStampMixin):
    """Structure tarifaire et échéances des frais de scolarité."""
    objects = scoped_manager('classroom__school')

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


PERIODICITY_CHOICES = [
    ('MOIS', 'Par mois'),
    ('TRIMESTRE', 'Par trimestre'),
    ('SEMESTRE', 'Par semestre'),
    ('ANNUEL', 'Par année'),
]


class TuitionFee(TimeStampMixin):
    """Frais de scolarité : défini par NIVEAU de classe et par périodicité.

    Chaque classe hérite du frais de son niveau ; le reçue et le reliquat
    se calculent à partir de cette grille officielle.
    """
    objects = SchoolManager()

    school = models.ForeignKey(
        'accounts.School',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='tuition_fees',
        verbose_name="École",
    )
    level = models.CharField(max_length=20, choices=ClassRoom.LEVEL_CHOICES, verbose_name="Niveau de classe")
    periodicity = models.CharField(max_length=12, choices=PERIODICITY_CHOICES, default='ANNUEL', verbose_name="Périodicité")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant (FCFA)")
    academic_year = models.CharField(max_length=20, default="2026-2027", verbose_name="Année académique")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Frais de scolarité (par niveau)"
        verbose_name_plural = "Frais de scolarité (par niveau)"
        unique_together = [('school', 'level', 'periodicity', 'academic_year')]
        ordering = ['level', 'periodicity']

    def __str__(self):
        return f"{self.get_level_display()} — {self.get_periodicity_display()} : {self.amount} FCFA"


class Expense(TimeStampMixin):
    """Dépense de l'école, classée par catégorie, filtrable par mois."""
    objects = SchoolManager()

    CATEGORIES = [
        ('SALAIRES', 'Salaires & personnel'),
        ('FOURNITURES', 'Fournitures & équipements'),
        ('MAINTENANCE', 'Maintenance & réparations'),
        ('UTILITES', 'Eau & électricité'),
        ('TRANSPORT', 'Transport'),
        ('COMMUNICATION', 'Communication & internet'),
        ('LOCATION', 'Loyer'),
        ('EVENEMENT', 'Événements & cérémonies'),
        ('AUTRE', 'Autres'),
    ]

    school = models.ForeignKey(
        'accounts.School',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='expenses',
        verbose_name="École",
    )
    category = models.CharField(max_length=20, choices=CATEGORIES, default='AUTRE', verbose_name="Catégorie")
    label = models.CharField(max_length=150, verbose_name="Libellé de la dépense")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant (FCFA)")
    expense_date = models.DateField(verbose_name="Date de la dépense")
    description = models.TextField(blank=True, null=True, verbose_name="Description")

    class Meta:
        verbose_name = "Dépense"
        verbose_name_plural = "Dépenses"
        ordering = ['-expense_date']

    def __str__(self):
        return f"{self.label} — {self.amount} FCFA"


class StudentPayment(TimeStampMixin):
    """
    Enregistrement de règlement / paiement effectué par un étudiant.
    Le reçu officiel est émis systématiquement (format A5 en PDF).
    """
    objects = scoped_manager('student__school')

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
    school = models.ForeignKey(
        'accounts.School',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='payments',
        verbose_name="École",
    )
    periodicity = models.CharField(max_length=12, choices=PERIODICITY_CHOICES, default='ANNUEL', verbose_name="Périodicité du paiement")
    period_label = models.CharField(max_length=60, blank=True, default='', verbose_name="Période concernée (ex : Octobre 2026, Trimestre 1)")
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
        """Suppression autorisée (correction/reversal comptable par l'admin)."""
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Reçu #{self.receipt_number} - {self.student.full_name} : {self.amount_paid} FCFA"

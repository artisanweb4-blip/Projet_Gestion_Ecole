"""
Modèles du module Notes & Bulletins.

Ce module s'appuie désormais sur les modèles « riches » du projet :
- classes.Class     → la classe
- courses.Subject   → la matière
- students.Student  → l'élève
Il définit uniquement les concepts propres aux évaluations :
année académique, période, évaluation et note.
"""
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from classes.models import Class
from courses.models import Subject
from students.models import Student


class AcademicYear(models.Model):
    name = models.CharField(max_length=20, unique=True, verbose_name="Année scolaire")
    start_date = models.DateField(verbose_name="Date de début")
    end_date = models.DateField(verbose_name="Date de fin")
    is_active = models.BooleanField(default=True, verbose_name="Année en cours")

    class Meta:
        verbose_name = "Année académique"
        verbose_name_plural = "Années académiques"
        ordering = ['-start_date']

    def __str__(self):
        return self.name


class Period(models.Model):
    """Période de notation : trimestre, semestre, mois..."""
    PERIOD_TYPES = [
        ('TRIMESTRE', 'Trimestre'),
        ('SEMESTRE', 'Semestre'),
        ('MENSUEL', 'Mensuel'),
        ('ANNUEL', 'Annuel'),
    ]

    name = models.CharField(max_length=50, verbose_name="Nom de la période")
    period_type = models.CharField(
        max_length=20, choices=PERIOD_TYPES, default='TRIMESTRE', verbose_name="Type"
    )
    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.CASCADE, related_name="periods",
        verbose_name="Année académique",
    )
    start_date = models.DateField(null=True, blank=True, verbose_name="Date de début")
    end_date = models.DateField(null=True, blank=True, verbose_name="Date de fin")

    class Meta:
        verbose_name = "Période"
        verbose_name_plural = "Périodes"
        ordering = ['academic_year', 'start_date', 'id']

    def __str__(self):
        return f"{self.name} - {self.academic_year.name}"


class Evaluation(models.Model):
    EVAL_TYPES = [
        ('DEVOIR', 'Devoir'),
        ('INTERRO', 'Interrogation'),
        ('COMPOSITION', 'Composition'),
        ('TP', 'Travaux Pratiques'),
        ('EXAMEN', 'Examen'),
    ]

    title = models.CharField(max_length=150, verbose_name="Titre")
    eval_type = models.CharField(
        max_length=20, choices=EVAL_TYPES, default='DEVOIR', verbose_name="Type"
    )
    classroom = models.ForeignKey(
        Class, on_delete=models.CASCADE, related_name="evaluations",
        verbose_name="Classe",
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="evaluations",
        verbose_name="Matière",
    )
    period = models.ForeignKey(
        Period, on_delete=models.CASCADE, related_name="evaluations",
        verbose_name="Période",
    )
    coefficient = models.PositiveSmallIntegerField(default=1, verbose_name="Coefficient")
    max_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=20.0, verbose_name="Barème"
    )
    date = models.DateField(verbose_name="Date")

    class Meta:
        verbose_name = "Évaluation"
        verbose_name_plural = "Évaluations"
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.classroom.name} | {self.subject.name} - {self.title}"


class Grade(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="grades",
        verbose_name="Élève",
    )
    evaluation = models.ForeignKey(
        Evaluation, on_delete=models.CASCADE, related_name="grades",
        verbose_name="Évaluation",
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Note",
    )
    appreciation = models.CharField(max_length=255, blank=True, verbose_name="Appréciation")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
        unique_together = ('student', 'evaluation')

    def clean(self):
        if self.score is not None and self.evaluation:
            if self.score > self.evaluation.max_score:
                raise ValidationError(
                    f"La note ({self.score}) dépasse le barème ({self.evaluation.max_score})."
                )

    def __str__(self):
        return f"{self.student.full_name}: {self.score if self.score is not None else 'N/A'}"

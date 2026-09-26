from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
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


class Classroom(models.Model):
    name = models.CharField(max_length=50, verbose_name="Nom de la classe")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="classrooms")

    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"
        unique_together = ('name', 'academic_year')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.academic_year.name})"


class Student(models.Model):
    matricule = models.CharField(max_length=30, unique=True, verbose_name="Matricule")
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="students")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Date de naissance")

    class Meta:
        verbose_name = "Élève"
        verbose_name_plural = "Élèves"
        ordering = ['last_name', 'first_name']

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_period_average(self, period_id):
        grades = self.grades.filter(
            evaluation__period_id=period_id,
            score__isnull=False
        ).select_related('evaluation')

        if not grades.exists():
            return None

        total_weighted_score = 0
        total_coefficients = 0

        for grade in grades:
            score_on_20 = (float(grade.score) / float(grade.evaluation.max_score)) * 20.0
            coeff = grade.evaluation.coefficient
            total_weighted_score += score_on_20 * coeff
            total_coefficients += coeff

        if total_coefficients == 0:
            return None

        return round(total_weighted_score / total_coefficients, 2)

    def __str__(self):
        return f"{self.full_name} ({self.matricule})"


class Subject(models.Model):
    code = models.CharField(max_length=10, unique=True, verbose_name="Code matière")
    name = models.CharField(max_length=100, verbose_name="Nom de la matière")

    class Meta:
        verbose_name = "Matière"
        verbose_name_plural = "Matières"

    def __str__(self):
        return self.name


class Period(models.Model):
    name = models.CharField(max_length=50, verbose_name="Nom de la période")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="periods")

    class Meta:
        verbose_name = "Période"
        verbose_name_plural = "Périodes"

    def __str__(self):
        return f"{self.name} - {self.academic_year.name}"


class Evaluation(models.Model):
    EVAL_TYPES = [
        ('DEVOIR', 'Devoir'),
        ('COMPOSITION', 'Composition'),
        ('TP', 'Travaux Pratiques'),
        ('INTERRO', 'Interrogation'),
    ]

    title = models.CharField(max_length=150, verbose_name="Titre")
    eval_type = models.CharField(max_length=20, choices=EVAL_TYPES, default='DEVOIR', verbose_name="Type")
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="evaluations")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="evaluations")
    period = models.ForeignKey(Period, on_delete=models.CASCADE, related_name="evaluations")
    coefficient = models.PositiveIntegerField(default=1, verbose_name="Coefficient")
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=20.0, verbose_name="Barème")
    date = models.DateField(verbose_name="Date")

    class Meta:
        verbose_name = "Évaluation"
        verbose_name_plural = "Évaluations"

    def __str__(self):
        return f"{self.classroom.name} | {self.subject.name} - {self.title}"


class Grade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="grades")
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name="grades")
    score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Note"
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
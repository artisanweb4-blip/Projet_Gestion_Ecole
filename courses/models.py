import uuid
from django.core.exceptions import ValidationError
from django.db import models
from core.models import TimeStampMixin


class Program(TimeStampMixin):
    code = models.CharField(
        max_length=20, unique=True, verbose_name="Code du programme"
    )
    name = models.CharField(max_length=250, verbose_name="Nom du programme")
    description = models.TextField(
        blank=True, null=True, verbose_name="Description"
    )

    class Meta:
        verbose_name = "Programme"
        verbose_name_plural = "Programmes"

    def __str__(self):
        return f"{self.code} - {self.name}"


class Subject(TimeStampMixin):
    name = models.CharField(max_length=150, verbose_name="Nom de la matière")
    code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Code",
    )

    class Meta:
        verbose_name = "Matière"
        verbose_name_plural = "Matières"

    def clean(self):
        super().clean()
        # Convertit les chaînes vides en None pour éviter le conflit d'unicité sur ""
        if self.code == "":
            self.code = None

    def save(self, *args, **kwargs):
        # Convertit la chaîne vide en None si présent
        if self.code == "":
            self.code = None

        # Génère automatiquement un code unique si le champ est laissé vide
        if not self.code:
            base_code = self.name[:4].upper() if self.name else "SUBJ"
            short_id = str(uuid.uuid4())[:4].upper()
            self.code = f"{base_code}-{short_id}"

        super().save(*args, **kwargs)

    def __str__(self):
        if self.code:
            return f"{self.code} - {self.name}"
        return self.name


class ProgramSubject(TimeStampMixin):
    program = models.ForeignKey(
        Program, on_delete=models.CASCADE, related_name='program_subjects'
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name='subject_programs'
    )

    # CORRECTION : Utilisation de la chaîne 'teachers.Teacher' pour éviter le circular import
    teacher = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_subjects',
        verbose_name="Enseignant titulaire",
    )

    coefficient = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.0, verbose_name="Coefficient"
    )
    hours_per_week = models.PositiveIntegerField(
        default=2, verbose_name="Heures/Semaine"
    )
    total_hours = models.PositiveIntegerField(
        default=30, verbose_name="Volume Horaire Total"
    )
    is_optional = models.BooleanField(
        default=False, verbose_name="Optionnelle ?"
    )

    class Meta:
        verbose_name = "Matière du programme"
        verbose_name_plural = "Matières des programmes"
        unique_together = ('program', 'subject')

    def __str__(self):
        teacher_name = f" - {self.teacher}" if self.teacher else ""
        return f"{self.subject.name} ({self.program.code}){teacher_name}"


class Course(TimeStampMixin):
    """Un cours : une matière enseignée à une classe par un enseignant."""
    code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        verbose_name="Code du cours",
    )
    name = models.CharField(max_length=150, verbose_name="Intitulé du cours")
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name="Matière",
    )
    school_class = models.ForeignKey(
        'classes.Class',
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name="Classe",
    )
    teacher = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name="Enseignant",
    )
    credits = models.PositiveSmallIntegerField(default=1, verbose_name="Crédits")
    coefficient = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.0,
        verbose_name="Coefficient",
    )
    description = models.TextField(blank=True, null=True, verbose_name="Description")

    class Meta:
        verbose_name = "Cours"
        verbose_name_plural = "Cours"
        unique_together = ('subject', 'school_class')

    def save(self, *args, **kwargs):
        if not self.code:
            import uuid
            base = self.subject.name[:4].upper() if self.subject and self.subject.name else "COUR"
            self.code = f"{base}-{str(uuid.uuid4())[:4].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subject.name} - {self.school_class.name} ({self.code})"


class Enrollment(TimeStampMixin):
    """Inscription d'un élève à un cours."""
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name="Cours",
    )
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name="Élève",
    )

    class Meta:
        verbose_name = "Inscription à un cours"
        verbose_name_plural = "Inscriptions aux cours"
        unique_together = ('course', 'student')

    def __str__(self):
        return f"{self.student.full_name} → {self.course.code}"
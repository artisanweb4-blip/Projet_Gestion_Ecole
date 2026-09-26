from django.db import models
from django.core.exceptions import ValidationError
from core.models import TimeStampMixin
from courses.models import Course
from students.models import Student as StudentProfile

class Exam(TimeStampMixin):
    """Examen d'évaluation (Partiel, Épreuve finale, Contrôle continu)."""
    EXAM_TYPES = (
        ('CC', 'Contrôle Continu'),
        ('PARTIAL', 'Examen Partiel'),
        ('FINAL', 'Examen Final'),
    )

    title = models.CharField(max_length=200, verbose_name="Titre de l'examen")
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES, default='CC', verbose_name="Type d'examen")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams', verbose_name="Cours concerné")
    date = models.DateTimeField(verbose_name="Date et heure de l'épreuve")
    duration_minutes = models.PositiveIntegerField(default=120, verbose_name="Durée (en minutes)")
    total_points = models.FloatField(default=20.0, verbose_name="Note maximale (sur 20 par défaut)")

    class Meta:
        verbose_name = "Examen"
        verbose_name_plural = "Examens"

    def __str__(self):
        return f"{self.title} - {self.course.code} ({self.get_exam_type_display()})"


class Question(TimeStampMixin):
    """Question rattachée à un examen (QCM, Texte, Fichier)."""
    QUESTION_TYPES = (
        ('MCQ', 'Question à Choix Multiple (QCM)'),
        ('TEXT', 'Réponse Rédactionnelle / Texte'),
        ('FILE', 'Soumission de fichier / Schéma'),
    )

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions', verbose_name="Examen")
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='TEXT', verbose_name="Type de question")
    text = models.TextField(verbose_name="Énoncé de la question")
    points = models.FloatField(default=2.0, verbose_name="Points de la question")
    options = models.TextField(blank=True, null=True, verbose_name="Options QCM (séparées par une virgule si QCM)")

    class Meta:
        verbose_name = "Question d'examen"
        verbose_name_plural = "Questions d'examen"

    def __str__(self):
        return f"[{self.get_question_type_display()}] {self.text[:50]}"


class ExamResult(TimeStampMixin):
    """Note obtenue par un étudiant à un examen."""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results', verbose_name="Examen")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='exam_results', verbose_name="Étudiant")
    score = models.FloatField(verbose_name="Note obtenue")
    remarks = models.TextField(blank=True, null=True, verbose_name="Appréciation / Remarques")

    class Meta:
        verbose_name = "Résultat d'examen"
        verbose_name_plural = "Résultats d'examens"
        constraints = [
            models.UniqueConstraint(fields=['exam', 'student'], name='unique_student_exam_result')
        ]

    def clean(self):
        super().clean()
        if self.score < 0 or self.score > self.exam.total_points:
            raise ValidationError(f"La note obtenue ({self.score}) doit être comprise entre 0 et {self.exam.total_points}.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name} : {self.score}/{self.exam.total_points} ({self.exam.title})"

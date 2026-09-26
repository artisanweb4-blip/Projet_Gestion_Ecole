from django.db import models
from django.core.exceptions import ValidationError
from core.models import TimeStampMixin
from courses.models import Course
from students.models import Student as StudentProfile

class Assignment(TimeStampMixin):
    """Devoir à rendre par les étudiants."""
    title = models.CharField(max_length=200, verbose_name="Titre du devoir")
    description = models.TextField(verbose_name="Consignes / Description")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments', verbose_name="Cours concerné")
    due_date = models.DateTimeField(verbose_name="Date et heure limite")
    attachment = models.FileField(upload_to='assignments/', blank=True, null=True, verbose_name="Pièce jointe du sujet")
    max_score = models.FloatField(default=20.0, verbose_name="Note maximale")

    class Meta:
        verbose_name = "Devoir"
        verbose_name_plural = "Devoirs"

    def __str__(self):
        return f"{self.title} ({self.course.code})"


class AssignmentSubmission(TimeStampMixin):
    """Rendu de devoir par un étudiant avec correction et note de l'enseignant."""
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions', verbose_name="Devoir")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='submissions', verbose_name="Étudiant")
    submission_text = models.TextField(blank=True, null=True, verbose_name="Réponse en ligne")
    submitted_file = models.FileField(upload_to='submissions/', blank=True, null=True, verbose_name="Fichier du devoir rendu")
    submission_date = models.DateTimeField(auto_now_add=True, verbose_name="Date de soumission")
    score = models.FloatField(blank=True, null=True, verbose_name="Note attribuée")
    feedback = models.TextField(blank=True, null=True, verbose_name="Commentaires / Feedback de l'enseignant")

    class Meta:
        verbose_name = "Soumission de devoir"
        verbose_name_plural = "Soumissions de devoirs"
        constraints = [
            models.UniqueConstraint(fields=['assignment', 'student'], name='unique_student_assignment_submission')
        ]

    def clean(self):
        super().clean()
        if self.score is not None:
            if self.score < 0 or self.score > self.assignment.max_score:
                raise ValidationError(f"La note doit être comprise entre 0 et {self.assignment.max_score}.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Soumission {self.student.full_name} - {self.assignment.title}"

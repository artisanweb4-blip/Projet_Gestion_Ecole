from django.db import models
from django.core.exceptions import ValidationError
from core.models import TimeStampMixin
from courses.models import Course
from teachers.models import TeacherProfile

class Semester(TimeStampMixin):
    """Semestre académique."""
    name = models.CharField(max_length=50, verbose_name="Semestre (ex: Semestre 1)")
    academic_year = models.CharField(max_length=20, default="2025-2026", verbose_name="Année Académique")
    start_date = models.DateField(verbose_name="Date de début")
    end_date = models.DateField(verbose_name="Date de fin")

    class Meta:
        verbose_name = "Semestre"
        verbose_name_plural = "Semestres"

    def __str__(self):
        return f"{self.name} ({self.academic_year})"


class ClassroomRoom(TimeStampMixin):
    """Salle de classe ou amphithéâtre."""
    code = models.CharField(max_length=30, unique=True, verbose_name="Code Salle")
    name = models.CharField(max_length=100, verbose_name="Nom de la salle / Amphi")
    building = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bâtiment / Pavillon")
    capacity = models.PositiveIntegerField(default=50, verbose_name="Capacité d'accueil")

    class Meta:
        verbose_name = "Salle de cours"
        verbose_name_plural = "Salles de cours"
        constraints = [
            models.UniqueConstraint(fields=['code'], name='unique_room_code')
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class TimeSlot(TimeStampMixin):
    """Créneau horaire de la semaine."""
    DAYS_OF_WEEK = (
        (1, 'Lundi'),
        (2, 'Mardi'),
        (3, 'Mercredi'),
        (4, 'Jeudi'),
        (5, 'Vendredi'),
        (6, 'Samedi'),
    )
    day = models.IntegerField(choices=DAYS_OF_WEEK, verbose_name="Jour de la semaine")
    start_time = models.TimeField(verbose_name="Heure de début")
    end_time = models.TimeField(verbose_name="Heure de fin")

    class Meta:
        verbose_name = "Créneau Horaire"
        verbose_name_plural = "Créneaux Horaires"
        constraints = [
            models.UniqueConstraint(fields=['day', 'start_time', 'end_time'], name='unique_timeslot_slot')
        ]

    def __str__(self):
        return f"{self.get_day_display()} : {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"


class Schedule(TimeStampMixin):
    """
    Planification d'un cours dans une salle et sur un créneau horaire.
    Contient la logique métier anti-chevauchement (Règles imposées).
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='schedules', verbose_name="Cours")
    room = models.ForeignKey(ClassroomRoom, on_delete=models.CASCADE, related_name='schedules', verbose_name="Salle")
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='schedules', verbose_name="Créneau Horaire")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='schedules', verbose_name="Semestre")

    class Meta:
        verbose_name = "Planification d'emploi du temps"
        verbose_name_plural = "Planifications d'emplois du temps"
        constraints = [
            models.UniqueConstraint(fields=['room', 'time_slot', 'semester'], name='unique_room_slot_semester'),
        ]

    def clean(self):
        super().clean()
        # Règle Métier 1 : La salle est déjà occupée sur ce créneau
        room_conflict = Schedule.objects.filter(
            room=self.room,
            time_slot=self.time_slot,
            semester=self.semester
        ).exclude(pk=self.pk)
        if room_conflict.exists():
            raise ValidationError(f"La salle '{self.room}' est déjà occupée le créneau sélectionné.")

        # Règle Métier 2 : Un enseignant ne peut pas être assigné à deux cours en même temps
        if self.course and self.course.teacher:
            teacher_conflict = Schedule.objects.filter(
                course__teacher=self.course.teacher,
                time_slot=self.time_slot,
                semester=self.semester
            ).exclude(pk=self.pk)
            if teacher_conflict.exists():
                raise ValidationError(f"L'enseignant {self.course.teacher} a déjà un cours programmé sur ce créneau horaire.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.course.code} | {self.room.code} | {self.time_slot}"

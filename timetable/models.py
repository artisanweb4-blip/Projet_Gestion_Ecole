from django.conf import settings
from django.db import models

from classes.models import Class  # Votre modèle de classe
from courses.models import Program, Subject  # Ajustez 'Subject' si besoin


class Classroom(models.Model):
    """Salles de cours, laboratoires ou amphithéâtres."""

    name = models.CharField(max_length=50, verbose_name='Nom de la salle')
    capacity = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Capacité d'accueil"
    )
    building = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Bâtiment / Bloc',
    )

    class Meta:
        verbose_name = 'Salle de cours'
        verbose_name_plural = 'Salles de cours'
        ordering = ['name']

    def __str__(self):
        return (
            f'{self.name} ({self.capacity} places)'
            if self.capacity
            else self.name
        )


class TimeSlot(models.Model):
    """Créneau horaire d'un cours pour une classe."""

    DAYS_OF_WEEK = [
        (1, 'Lundi'),
        (2, 'Mardi'),
        (3, 'Mercredi'),
        (4, 'Jeudi'),
        (5, 'Vendredi'),
        (6, 'Samedi'),
        (7, 'Dimanche'),
    ]

    school_class = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='time_slots',
        verbose_name='Classe',
    )
    subject = models.ForeignKey(
        Subject,  # Utilisez le nom exact de votre modèle de matière
        on_delete=models.CASCADE,
        related_name='time_slots',
        verbose_name='Matière',
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teaching_slots',
        verbose_name='Enseignant',
    )
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='time_slots',
        verbose_name='Salle',
    )

    day_of_week = models.IntegerField(
        choices=DAYS_OF_WEEK, verbose_name='Jour de la semaine'
    )
    start_time = models.TimeField(verbose_name='Heure de début')
    end_time = models.TimeField(verbose_name='Heure de fin')

    class Meta:
        verbose_name = 'Créneau horaire'
        verbose_name_plural = 'Créneaux horaires'
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.school_class} - {self.subject} ({self.get_day_of_week_display()} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')})"
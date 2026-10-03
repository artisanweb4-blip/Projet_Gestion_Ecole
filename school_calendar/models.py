from django.db import models

from core.scoping import SchoolManager, scoped_manager
from courses.models import Program


class EventCategory(models.Model):
    objects = SchoolManager()

    school = models.ForeignKey(
        'accounts.School',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='event_categories',
        verbose_name="École",
    )
    name = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    color = models.CharField(
        max_length=7, default="#3B82F6", verbose_name="Couleur Hex (ex: #3B82F6)"
    )

    class Meta:
        verbose_name = "Catégorie d'événement"
        verbose_name_plural = "Catégories d'événements"

    def __str__(self):
        return self.name


class AcademicEvent(models.Model):
    objects = SchoolManager()

    school = models.ForeignKey(
        'accounts.School',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='academic_events',
        verbose_name="École",
    )
    title = models.CharField(max_length=200, verbose_name="Titre")
    category = models.ForeignKey(
        EventCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
        verbose_name="Catégorie",
    )
    programs = models.ManyToManyField(
        Program, blank=True, related_name="events", verbose_name="Programmes / Classes"
    )
    start_date = models.DateTimeField(verbose_name="Date de début")
    end_date = models.DateTimeField(verbose_name="Date de fin")
    is_all_day = models.BooleanField(
        default=False, verbose_name="Toute la journée"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Description")

    class Meta:
        verbose_name = "Événement académique"
        verbose_name_plural = "Événements académiques"
        ordering = ["start_date"]

    def __str__(self):
        return self.title
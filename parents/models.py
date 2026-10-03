# parents/models.py
from django.db import models

from core.scoping import SchoolManager, scoped_manager

class Parent(models.Model):
    objects = SchoolManager()

    school = models.ForeignKey(
        'accounts.School',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='parents',
        verbose_name="École",
    )
    CIVILITY_CHOICES = [
        ('M', 'Monsieur'),
        ('Mme', 'Madame'),
    ]

    civility = models.CharField(max_length=5, choices=CIVILITY_CHOICES, default='M', verbose_name="Civilité")
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    email = models.EmailField(unique=True, verbose_name="Email")
    phone = models.CharField(max_length=20, verbose_name="Téléphone")
    address = models.TextField(blank=True, null=True, verbose_name="Adresse")
    profession = models.CharField(max_length=100, blank=True, null=True, verbose_name="Profession")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_civility_display()} {self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Parent d'élève"
        verbose_name_plural = "Parents d'élèves"
        ordering = ['last_name', 'first_name']
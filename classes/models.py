from django.db import models
from core.models import TimeStampMixin


class Class(TimeStampMixin):
    LEVEL_CHOICES = [
        # --- Cycle Fondamental / Collège ---
        ('1ère', '1ère année'),
        ('2ème', '2ème année'),
        ('3ème', '3ème année'),
        ('4ème', '4ème année'),
        ('5ème', '5ème année'),
        ('6ème', '6ème année'),
        ('7ème', '7ème année'),
        ('8ème', '8ème année'),
        ('9ème', '9ème année'),
        
        # --- Secondary / Lycée ---
        ('10ème', '10ème Année (Seconde)'),
        ('11ème', '11ème Année (Première)'),
        ('12ème', '12ème Année (Terminal)'),
        ('Seconde', 'Seconde'),
        ('Première', 'Première'),
        ('Terminale', 'Terminale'),

        # --- Superior / Université ---
        ('L1', 'Licence 1'),
        ('L2', 'Licence 2'),
        ('L3', 'Licence 3'),
        ('M1', 'Master 1'),
        ('M2', 'Master 2'),
        ('Doctorat', 'Doctorat'),
    ]

    SECTION_CHOICES = [
        ('Française', 'Française'),
        ('Arabe', 'Arabe'),
        ('Mixte', 'Mixte'),
    ]

    name = models.CharField(max_length=100, verbose_name="Nom de la classe")
    
    program = models.ForeignKey(
        'courses.Program',
        on_delete=models.CASCADE,
        related_name='classes',
        null=True,
        blank=True,
        verbose_name='Programme / Filière',
    )
    
    level = models.CharField(
        max_length=20, choices=LEVEL_CHOICES, verbose_name="Niveau"
    )
    section = models.CharField(
        max_length=20,
        choices=SECTION_CHOICES,
        default='Française',
        verbose_name="Section",
    )
    capacity = models.PositiveIntegerField(
        default=30, verbose_name="Capacité"
    )
    room = models.CharField(
        max_length=20, blank=True, verbose_name="Salle"
    )

    responsible = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='classes_managed',
        verbose_name="Responsable",
    )

    is_active = models.BooleanField(
        default=True, verbose_name="Classe active"
    )

    class Meta:
        ordering = ['level', 'name']
        verbose_name = "Classe"
        verbose_name_plural = "Classes"

    def __str__(self):
        program_name = f" - {self.program.name}" if self.program else ""
        return f"{self.name} ({self.get_level_display()}{program_name})"

    @property
    def student_count(self):
        return self.students.filter(is_active=True).count()
from datetime import date
from django.db import models
from django.contrib.auth import get_user_model
from core.models import TimeStampMixin

User = get_user_model()


class Teacher(TimeStampMixin):
    user = models.OneToOneField(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='teacher_profile'
    )
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    photo = models.ImageField(upload_to='teachers/photos/', blank=True, null=True, verbose_name="Photo")
    employee_id = models.CharField(max_length=20, unique=True, blank=True, verbose_name="Matricule")
    specialization = models.CharField(max_length=100, verbose_name="Spécialité / Matière")
    hire_date = models.DateField(verbose_name="Date d'embauche")
    phone = models.CharField(max_length=20, verbose_name="Téléphone")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = "Enseignant"
        verbose_name_plural = "Enseignants"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    # --- Aliases de compatibilité pour les templates ---
    @property
    def subject(self):
        """Permet au template d'utiliser {{ teacher.subject }} sans erreur."""
        return self.specialization

    @property
    def matricule(self):
        """Permet au template d'utiliser {{ teacher.matricule }} sans erreur."""
        return self.employee_id

    # --- Génération automatique du matricule ---
    def save(self, *args, **kwargs):
        if not self.employee_id:
            last_teacher = Teacher.objects.all().order_by('id').last()
            num = 1
            if last_teacher and last_teacher.employee_id:
                try:
                    num = int(last_teacher.employee_id.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = Teacher.objects.count() + 1
            
            year = self.hire_date.year if self.hire_date else date.today().year
            self.employee_id = f"ENS-{year}-{num:04d}"

        super().save(*args, **kwargs)
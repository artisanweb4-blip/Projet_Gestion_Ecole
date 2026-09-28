from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from core.models import TimeStampMixin

class UserManager(BaseUserManager):
    """Gestionnaire personnalisé pour la création d'utilisateurs et superutilisateurs."""
    def create_user(self, email, username, password=None, role='STUDENT', **extra_fields):
        if not email:
            raise ValueError("L'adresse e-mail est obligatoire.")
        if not username:
            raise ValueError("Le nom d'utilisateur est obligatoire.")

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Le superutilisateur doit avoir is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Le superutilisateur doit avoir is_superuser=True.")

        return self.create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampMixin):
    """
    Modèle utilisateur personnalisé avec gestion fine des rôles scolaires.
    """
    ROLE_CHOICES = (
        ('ADMIN', 'Administrateur / Direction'),
        ('COMPTABLE', 'Comptable'),
        ('TEACHER', 'Enseignant'),
        ('STUDENT', 'Étudiant'),
        ('PARENT', 'Parent d\'élève'),
    )

    email = models.EmailField(unique=True, verbose_name="Adresse Email")
    username = models.CharField(max_length=150, unique=True, verbose_name="Nom d'utilisateur")
    first_name = models.CharField(max_length=150, verbose_name="Prénom")
    last_name = models.CharField(max_length=150, verbose_name="Nom de famille")
    phone = models.CharField(max_length=30, blank=True, null=True, verbose_name="Téléphone")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT', verbose_name="Rôle dans l'établissement")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Photo de profil")

    is_staff = models.BooleanField(default=False, verbose_name="Membre du staff")
    is_active = models.BooleanField(default=True, verbose_name="Compte actif")

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        constraints = [
            models.UniqueConstraint(fields=['email'], name='unique_user_email'),
            models.UniqueConstraint(fields=['username'], name='unique_user_username'),
        ]

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

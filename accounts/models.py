from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from core.models import TimeStampMixin


class School(TimeStampMixin):
    """École (tenant) inscrite sur la plateforme GCE."""
    PLAN_CHOICES = [
        ('GRATUIT', 'Gratuit'),
        ('STANDARD', 'Standard'),
        ('PREMIUM', 'Premium'),
    ]

    name = models.CharField(max_length=150, unique=True, verbose_name="Nom de l'école")
    code = models.SlugField(max_length=30, unique=True, blank=True, verbose_name="Code")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Adresse")
    phone = models.CharField(max_length=30, blank=True, null=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, null=True, verbose_name="Email de contact")
    plan = models.CharField(max_length=10, choices=PLAN_CHOICES, default='STANDARD',
                            verbose_name="Formule")
    subscription = models.ForeignKey(
        'SubscriptionPlan',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='schools',
        verbose_name="Abonnement",
    )
    subscription_until = models.DateField(
        null=True, blank=True,
        verbose_name="Abonnement valable jusqu'au",
    )

    class Meta:
        verbose_name = "École (plateforme)"
        verbose_name_plural = "Écoles (plateforme)"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.code:
            from django.utils.text import slugify
            import uuid
            base = slugify(self.name)[:20].strip('-') or 'ecole'
            self.code = f"{base}-{str(uuid.uuid4())[:5]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


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

    GENDER_CHOICES = (
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    )

    REGION_CHOICES = (
        ('Bamako', 'District de Bamako'),
        ('Kayes', 'Kayes'),
        ('Koulikoro', 'Koulikoro'),
        ('Sikasso', 'Sikasso'),
        ('Ségou', 'Ségou'),
        ('Mopti', 'Mopti'),
        ('Gao', 'Gao'),
        ('Tombouctou', 'Tombouctou'),
        ('Kidal', 'Kidal'),
        ('Ménaka', 'Ménaka'),
        ('Taoudénit', 'Taoudénit'),
        ('Hors Mali', 'Hors Mali'),
    )

    email = models.EmailField(unique=True, verbose_name="Adresse Email")
    username = models.CharField(max_length=150, unique=True, verbose_name="Nom d'utilisateur")
    first_name = models.CharField(max_length=150, verbose_name="Prénom")
    last_name = models.CharField(max_length=150, verbose_name="Nom de famille")
    phone = models.CharField(max_length=30, blank=True, null=True, verbose_name="Téléphone")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT', verbose_name="Rôle dans l'établissement")
    gender = models.CharField(
        max_length=1, choices=GENDER_CHOICES, blank=True,
        verbose_name="Sexe",
    )
    region = models.CharField(
        max_length=50, choices=REGION_CHOICES, blank=True,
        verbose_name="Région",
    )
    school = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name="École (rattachement)",
    )
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


class SubscriptionPlan(TimeStampMixin):
    """Formule d'abonnement proposée aux écoles par la plateforme."""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom de la formule")
    code = models.SlugField(max_length=30, unique=True, blank=True, verbose_name="Code")
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Prix (FCFA / période)",
    )
    duration_days = models.PositiveIntegerField(
        default=30, verbose_name="Durée (jours)",
    )
    max_students = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Plafond d'élèves (vide = illimité)",
    )
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    features = models.TextField(
        blank=True, null=True,
        verbose_name="Fonctionnalités incluses",
        help_text="Une fonctionnalité par ligne.",
    )
    is_active = models.BooleanField(default=True, verbose_name="Proposée à l'inscription")

    class Meta:
        verbose_name = "Abonnement"
        verbose_name_plural = "Abonnements"
        ordering = ['price']

    def save(self, *args, **kwargs):
        if not self.code:
            from django.utils.text import slugify
            self.code = slugify(self.name)[:30].strip('-') or 'formule'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({int(self.price)} FCFA)"


class PlatformSetting(TimeStampMixin):
    """Paramètres généraux de la plateforme (singleton)."""
    platform_name = models.CharField(
        max_length=150, default="Gestion d'École",
        verbose_name="Nom de la plateforme",
    )
    support_email = models.EmailField(blank=True, null=True, verbose_name="Email du support")
    public_registration_enabled = models.BooleanField(
        default=True,
        verbose_name="Autoriser l'inscription publique des écoles",
    )
    default_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='default_for_settings',
        verbose_name="Abonnement attribué par défaut",
    )

    class Meta:
        verbose_name = "Paramètre de la plateforme"
        verbose_name_plural = "Paramètres de la plateforme"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.platform_name

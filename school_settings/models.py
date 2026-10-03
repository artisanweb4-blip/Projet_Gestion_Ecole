from django.db import models

from core.scoping import NO_ACCESS, get_current_school


class GeneralSetting(models.Model):
    """Configuration générale du système scolaire (Singleton)."""

    country_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Nom du Pays",
    )
    motto = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Devise du Pays",
    )
    ministry = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Ministère tutelle",
    )
    directorate = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Direction tutelle",
    )
    director_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Nom du Directeur",
    )
    current_academic_year = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Année scolaire actuelle",
    )
    is_bilingual = models.BooleanField(
        default=False,
        verbose_name="Système bilingue (support français-arabe)",
    )

    class Meta:
        verbose_name = "Paramètre Général"
        verbose_name_plural = "Paramètres Généraux"

    def save(self, *args, **kwargs):
        # Compatibilité : la ligne héritée (hors école) garde l'identifiant 1.
        if self.school_id is None and not self.pk:
            self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls, school=None):
        """Paramètres de l'école courante (créés au besoin).

        Hors contexte d'école (site public, commandes) : ligne héritée.
        """
        if school is None:
            current = get_current_school()
            school = None if current == NO_ACCESS else current
        if school is not None:
            obj, _ = cls.objects.get_or_create(school=school)
            return obj
        obj = cls.objects.filter(school__isnull=True).first() or cls.objects.first()
        if obj is None:
            obj = cls.objects.create(pk=1)
        return obj

    def __str__(self):
        return "Configuration Générale"


class SchoolSetting(models.Model):
    """Informations de l'établissement (une ligne par école inscrite)."""

    school = models.OneToOneField(
        'accounts.School',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='settings',
        verbose_name="École",
    )

    logo = models.ImageField(
        upload_to='school/',
        blank=True,
        null=True,
        verbose_name="Logo de l'établissement",
        help_text="Format recommandé: PNG ou JPG, dimensions carrées",
    )
    school_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Nom de l'école",
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Adresse",
    )
    phone = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Téléphone",
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Email",
    )

    class Meta:
        verbose_name = "Information de l'école"
        verbose_name_plural = "Informations de l'école"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.school_name or "Configuration de l'école"


class NotificationSetting(models.Model):
    """Paramètres des notifications (Singleton)."""

    email_notifications = models.BooleanField(
        default=True, verbose_name="Notifications par email"
    )
    sms_notifications = models.BooleanField(
        default=False, verbose_name="Notifications SMS"
    )

    class Meta:
        verbose_name = "Paramètre de notification"
        verbose_name_plural = "Paramètres de notification"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class BackupSetting(models.Model):
    """Paramètres des sauvegardes (Singleton)."""

    auto_backup = models.BooleanField(
        default=True, verbose_name="Sauvegarde automatique"
    )
    last_backup_date = models.DateTimeField(
        blank=True, null=True, verbose_name="Dernière sauvegarde"
    )

    class Meta:
        verbose_name = "Paramètre de sauvegarde"
        verbose_name_plural = "Paramètres de sauvegarde"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
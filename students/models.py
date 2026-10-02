from datetime import date
from io import BytesIO
from PIL import Image
import qrcode
import barcode
from barcode.writer import ImageWriter

from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import TimeStampMixin

User = get_user_model()


class Student(TimeStampMixin):
    # --- Choices ---
    GENDER_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]

    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]

    # --- Informations personnelles ---
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_profile',
        verbose_name='Compte utilisateur',
    )
    first_name = models.CharField(max_length=100, verbose_name='Prénom')
    last_name = models.CharField(max_length=100, verbose_name='Nom')
    student_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name='Matricule',
    )
    photo = models.ImageField(
        upload_to='students/photos/',
        blank=True,
        null=True,
        verbose_name='Photo',
    )
    qr_code = models.ImageField(
        upload_to='students/qrcodes/',
        blank=True,
        null=True,
        verbose_name='QR Code',
    )
    barcode = models.ImageField(
        upload_to='students/barcodes/',
        blank=True,
        null=True,
        verbose_name='Code-barres',
    )

    # --- État civil ---
    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES, verbose_name='Sexe'
    )
    date_of_birth = models.DateField(verbose_name='Date de naissance')
    place_of_birth = models.CharField(
        max_length=100, verbose_name='Lieu de naissance'
    )
    nationality = models.CharField(
        max_length=50, default='Mali', verbose_name='Nationalité'
    )
    religion = models.CharField(
        max_length=50, blank=True, verbose_name='Religion'
    )

    # --- Contact ---
    address = models.TextField(verbose_name='Adresse')
    phone = models.CharField(max_length=20, verbose_name='Téléphone')
    email = models.EmailField(blank=True, null=True, verbose_name='Email')

    # --- Santé ---
    blood_group = models.CharField(
        max_length=5,
        choices=BLOOD_GROUP_CHOICES,
        blank=True,
        null=True,
        verbose_name='Groupe sanguin',
    )
    allergies = models.TextField(blank=True, null=True, verbose_name='Allergies')
    medical_notes = models.TextField(
        blank=True, null=True, verbose_name='Antécédents médicaux'
    )
    emergency_contact_name = models.CharField(
        max_length=100, verbose_name='Personne à contacter en urgence'
    )
    emergency_contact_phone = models.CharField(
        max_length=20, verbose_name="Téléphone d'urgence"
    )

    # --- Scolarité ---
    class_group = models.ForeignKey(
        'classes.Class',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name='Classe',
    )
    parents = models.ManyToManyField(
        'parents.Parent',
        blank=True,
        related_name='children',
        verbose_name='Parents / Tuteurs',
    )
    enrollment_date = models.DateField(
        default=date.today, verbose_name="Date d'inscription"
    )
    is_active = models.BooleanField(default=True, verbose_name='Actif')

    # --- Documents numérisés ---
    documents = models.FileField(
        upload_to='students/documents/',
        blank=True,
        null=True,
        verbose_name='Documents scannés',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Élève'
        verbose_name_plural = 'Élèves'

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.student_id or "Sans matricule"})'

    # --- Aliases / Propriétés de compatibilité ---
    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def matricule(self):
        return self.student_id

    @property
    def registration_number(self):
        return self.student_id

    @property
    def birth_date(self):
        return self.date_of_birth

    # --- Surcharges & Logique métiers ---
    def save(self, *args, **kwargs):
        # 1. Génération du matricule
        if not self.student_id:
            current_year = self.enrollment_date.year if self.enrollment_date else date.today().year
            prefix = f'STD-{current_year}-'
            
            last_student = (
                Student.objects.filter(student_id__startswith=prefix)
                .order_by('student_id')
                .last()
            )

            if last_student and last_student.student_id:
                try:
                    num = int(last_student.student_id.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1

            self.student_id = f'{prefix}{num:04d}'

        # 2. Génération automatique du QR Code
        if not self.qr_code and self.student_id:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=6,
                border=4,
            )
            qr.add_data(self.student_id)
            qr.make(fit=True)
            img = qr.make_image(fill_color='black', back_color='white')

            buffer = BytesIO()
            img.save(buffer, format='PNG')
            self.qr_code.save(
                f'qr_{self.student_id}.png', File(buffer), save=False
            )

        # 3. Génération automatique du Code-barres
        if not self.barcode and self.student_id:
            code128 = barcode.get_barcode_class('code128')
            barcode_instance = code128(self.student_id, writer=ImageWriter())

            buffer = BytesIO()
            barcode_instance.write(buffer)

            self.barcode.save(
                f'barcode_{self.student_id}.png', File(buffer), save=False
            )

        super().save(*args, **kwargs)
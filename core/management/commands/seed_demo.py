"""
Peuplement de la base avec des données de démonstration réalistes.

Usage : python manage.py seed_demo  (ou python seed_data.py)
Idempotent : peut être relancé sans créer de doublons.
"""
import random
from datetime import date, datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from classes.models import Class
from courses.models import Program, ProgramSubject, Subject
from finance.models import FeeStructure, StudentPayment
from grades.models import AcademicYear, Evaluation, Grade, Period
from school_calendar.models import AcademicEvent, EventCategory
from school_settings.models import SchoolSetting
from students.models import Student
from teachers.models import Teacher

random.seed(42)

SUBJECTS = [
    ("MATH", "Mathématiques", 4),
    ("FRAN", "Français", 4),
    ("ANGL", "Anglais", 2),
    ("SVT", "Sciences de la Vie et de la Terre", 2),
    ("HIST", "Histoire-Géographie", 2),
    ("INFO", "Informatique", 1),
    ("ARAB", "Arabe", 2),
    ("EPS", "Éducation Physique et Sportive", 1),
]

CLASSES = [
    ("6ème A", "6ème", "Française", "Salle 101"),
    ("5ème B", "5ème", "Française", "Salle 102"),
    ("Terminale C", "Terminale", "Française", "Salle 205"),
]

STUDENT_NAMES = [
    ("Awa", "DIALLO"), ("Moussa", "TRAORE"), ("Fatou", "NDIAYE"), ("Ibrahim", "KEITA"),
    ("Aminata", "SOW"), ("Cheikh", "FALL"), ("Mariam", "COULIBALY"), ("Ousmane", "KANE"),
    ("Khadija", "BA"), ("Adama", "CAMARA"), ("Aïssata", "BARRY"), ("Mamadou", "SY"),
    ("Rokia", "SANOGO"), ("Boubacar", "DIAKITE"), ("Salimata", "TOURE"), ("Yacouba", "SISSOKO"),
    ("Bintou", "KONE"), ("Seydou", "OUATTARA"), ("Nafissatou", "CEESAY"), ("Lansana", "KOUYATE"),
    ("Djeneba", "DIMBERTE"), ("Abdoulaye", "NDAW"), ("Mariama", "GUEYE"), ("Souleymane", "NDIAYE"),
    ("Assa", "MAIGA"), ("Modibo", "SIDIBE"), ("Fanta", "DRABO"), ("Ismaila", "THIAM"),
    ("Ramata", "ZONGO"), ("Karim", "OUEDRAOGO"),
]

TEACHER_NAMES = [
    ("Ousmane", "KANE", "Mathématiques"),
    ("Awa", "DIALLO", "Français"),
    ("Paul", "MBAPPE", "Anglais"),
    ("Mariama", "SAWADOGO", "Sciences de la Vie et de la Terre"),
    ("Amadou", "HAMIDOU", "Histoire-Géographie"),
    ("Rachid", "MOUSSA", "Arabe"),
]


class Command(BaseCommand):
    help = "Crée des données de démonstration (école, classes, élèves, notes...)."

    def handle(self, *args, **options):
        self.stdout.write("[+] Peuplement de la base de données (démo GCE)...")

        # ------------------------------------------------------------------
        # 0. Paramètres de l'établissement
        # ------------------------------------------------------------------
        school = SchoolSetting.load()
        school.school_name = "Collège Polyvalent Bilingue de la Réussite"
        school.address = "Quartier Nkolbisson, Yaoundé, Cameroun"
        school.phone = "+237 6 99 12 34 56"
        school.email = "contact@cpbr-cm.edu"
        school.save()
        self.stdout.write("  [OK] Paramètres de l'école")

        # ------------------------------------------------------------------
        # 1. Année académique & périodes
        # ------------------------------------------------------------------
        year, _ = AcademicYear.objects.get_or_create(
            name="2025-2026",
            defaults={"start_date": date(2025, 9, 15), "end_date": date(2026, 7, 10),
                      "is_active": True},
        )
        AcademicYear.objects.exclude(pk=year.pk).update(is_active=False)

        periods = {}
        for name, start, end in [
            ("1er Trimestre", date(2025, 9, 15), date(2025, 12, 19)),
            ("2ème Trimestre", date(2026, 1, 5), date(2026, 3, 27)),
            ("3ème Trimestre", date(2026, 4, 6), date(2026, 7, 10)),
        ]:
            periods[name], _ = Period.objects.get_or_create(
                name=name, academic_year=year,
                defaults={"period_type": "TRIMESTRE", "start_date": start, "end_date": end},
            )
        self.stdout.write(f"  [OK] Année {year.name} + {len(periods)} trimestres")

        # ------------------------------------------------------------------
        # 2. Programme & matières
        # ------------------------------------------------------------------
        program, _ = Program.objects.get_or_create(
            code="COL-FR", defaults={"name": "Cycle collégial - Section Française",
                                     "description": "Programme officiel de la section française."}
        )
        subjects = {}
        for code, name, coef in SUBJECTS:
            subject, _ = Subject.objects.get_or_create(code=code, defaults={"name": name})
            subjects[name] = subject
            ProgramSubject.objects.get_or_create(
                program=program, subject=subject,
                defaults={"coefficient": coef, "hours_per_week": min(6, coef + 1)},
            )
        self.stdout.write(f"  [OK] Programme « {program.name} » + {len(subjects)} matières")

        # ------------------------------------------------------------------
        # 3. Enseignants (+ comptes utilisateurs)
        # ------------------------------------------------------------------
        from accounts.models import User

        teachers = []
        for idx, (first, last, specialty) in enumerate(TEACHER_NAMES, start=1):
            teacher_user, _ = User.objects.get_or_create(
                email=f"{first.lower()}.{last.lower()}@cpbr-cm.edu",
                defaults={
                    "username": f"{first.lower()}.{last.lower()}",
                    "first_name": first, "last_name": last,
                    "role": "TEACHER", "phone": f"+237 6 70 00 0{idx} {idx}0",
                },
            )
            teacher_user.set_password("prof123")
            teacher_user.save()

            teacher, _ = Teacher.objects.get_or_create(
                employee_id=f"ENS-{idx:03d}",
                defaults={
                    "user": teacher_user, "first_name": first, "last_name": last,
                    "specialization": specialty, "hire_date": date(2019 + (idx % 5), 9, 1),
                    "phone": f"+237 6 70 00 0{idx} {idx}0",
                    "email": teacher_user.email,
                },
            )
            teachers.append(teacher)
        self.stdout.write(f"  [OK] {len(teachers)} enseignants")

        # ------------------------------------------------------------------
        # 4. Classes & élèves
        # ------------------------------------------------------------------
        classes = []
        for idx, (name, level, section, room) in enumerate(CLASSES):
            klass, _ = Class.objects.get_or_create(
                name=name,
                defaults={
                    "level": level, "section": section, "room": room,
                    "capacity": 40, "program": program,
                    "responsible": teachers[idx % len(teachers)],
                },
            )
            classes.append(klass)

        student_index = 0
        for c_idx, klass in enumerate(classes):
            for i in range(10):
                first, last = STUDENT_NAMES[student_index % len(STUDENT_NAMES)]
                student_index += 1
                gender = "F" if first.endswith(("a", "e")) and first[0] in "AFRMKDSB" else "M"
                if first in ("Awa", "Fatou", "Aminata", "Mariam", "Khadija", "Aïssata",
                             "Rokia", "Salimata", "Bintou", "Djeneba", "Fanta", "Ramata",
                             "Assa", "Mariama", "Nafissatou"):
                    gender = "F"
                Student.objects.get_or_create(
                    first_name=first, last_name=last, date_of_birth=date(
                        2014 - c_idx * 3, (student_index % 12) + 1, (student_index % 27) + 1
                    ),
                    defaults={
                        "gender": gender,
                        "class_group": klass,
                        "place_of_birth": "Yaoundé",
                        "nationality": "Cameroun",
                        "address": "Quartier Nkolbisson, Yaoundé",
                        "phone": f"+237 6 5{c_idx} {student_index:02d} {student_index:02d} {student_index % 10:02d} {student_index % 10:02d}",
                        "emergency_contact_name": f"M. {last}",
                        "emergency_contact_phone": "+237 6 99 88 77 66",
                        "enrollment_date": date(2025, 9, 15),
                    },
                )
        self.stdout.write(f"  [OK] {Student.objects.count()} élèves répartis dans {len(classes)} classes")

        # ------------------------------------------------------------------
        # 4b. Parents d'élèves + liaison parents ↔ élèves (1 → N)
        # ------------------------------------------------------------------
        from parents.models import Parent

        PARENTS = [
            ("M", "Oumar", "MAIGA", "oumarm856@gmail.com", "78765643", "Prof Histoire-Géographie", "Djélibougou"),
            ("Mme", "Fatoumata", "DIALLO", "fatoumata.diallo@gmail.com", "76554433", "Commerçante", "Kalaban Coura"),
            ("M", "Seydou", "TRAORE", "seydou.traore@gmail.com", "70112233", "Fonctionnaire", "Badalabougou"),
            ("Mme", "Kadiatou", "SOW", "kadiatou.sow@gmail.com", "76998877", "Couturière", "Sikoro"),
        ]
        parents_objs = []
        for civ, first, last, email, phone, job, addr in PARENTS:
            parent, _ = Parent.objects.get_or_create(
                email=email,
                defaults={"civility": civ, "first_name": first, "last_name": last,
                          "phone": phone, "profession": job, "address": addr},
            )
            parents_objs.append(parent)

        students_list = list(Student.objects.filter(is_active=True).order_by("id"))
        # Un parent peut avoir plusieurs enfants : affectation en cascade
        for idx, student in enumerate(students_list):
            student.parents.add(parents_objs[idx % len(parents_objs)])
            if idx % 7 == 3 and idx + 1 < len(students_list):
                # Fratrie : le même parent supplémentaire pour certains élèves
                student.parents.add(parents_objs[(idx + 1) % len(parents_objs)])
        self.stdout.write(f"  [OK] {len(parents_objs)} parents liés aux élèves (1 → N)")

        # ------------------------------------------------------------------
        # 5. Évaluations & notes (1er trimestre)
        # ------------------------------------------------------------------
        p1 = periods["1er Trimestre"]
        eval_count = 0
        for klass in classes:
            for subject_name in ["Mathématiques", "Français", "Anglais", "Informatique"]:
                subject = subjects[subject_name]
                for eval_idx in range(2):
                    evaluation, created = Evaluation.objects.get_or_create(
                        title=f"Devoir n°{eval_idx + 1}",
                        classroom=klass, subject=subject, period=p1,
                        defaults={
                            "eval_type": "DEVOIR",
                            "coefficient": 1 + eval_idx,
                            "max_score": 20,
                            "date": date(2025, 10, 14) + timedelta(days=eval_idx * 21),
                        },
                    )
                    if created:
                        eval_count += 1
                    # Notes déjà saisies pour les évaluations passées
                    if not evaluation.grades.exists():
                        base = random.uniform(8, 15)
                        for student in klass.students.all():
                            score = max(2, min(19.5, base + random.uniform(-4, 4)))
                            Grade.objects.get_or_create(
                                student=student, evaluation=evaluation,
                                defaults={"score": round(score * 4) / 4},
                            )
        self.stdout.write(f"  [OK] {eval_count} évaluations + {Grade.objects.count()} notes (1er trimestre)")

        # ------------------------------------------------------------------
        # 6. Calendrier académique
        # ------------------------------------------------------------------
        cat, _ = EventCategory.objects.get_or_create(
            name="Événement scolaire", defaults={"color": "#059669"}
        )
        exams_cat, _ = EventCategory.objects.get_or_create(
            name="Examens", defaults={"color": "#dc2626"}
        )
        AcademicEvent.objects.get_or_create(
            title="Composition du 1er Trimestre",
            category=exams_cat,
            defaults={
                "start_date": timezone.make_aware(datetime(2025, 12, 8, 8, 0)),
                "end_date": timezone.make_aware(datetime(2025, 12, 19, 17, 0)),
                "description": "Épreuves de composition pour toutes les classes.",
            },
        )
        AcademicEvent.objects.get_or_create(
            title="Vacances de fin de trimestre",
            category=cat,
            defaults={
                "start_date": timezone.make_aware(datetime(2025, 12, 20, 0, 0)),
                "end_date": timezone.make_aware(datetime(2026, 1, 4, 23, 59)),
                "is_all_day": True,
            },
        )
        AcademicEvent.objects.get_or_create(
            title="Journée porte ouverte",
            category=cat,
            defaults={
                "start_date": timezone.make_aware(datetime(2026, 2, 14, 9, 0)),
                "end_date": timezone.make_aware(datetime(2026, 2, 14, 17, 0)),
                "description": "Les parents sont invités à découvrir les travaux des élèves.",
            },
        )
        self.stdout.write("  [OK] Calendrier académique")

        # ------------------------------------------------------------------
        # 7. Frais & paiements
        # ------------------------------------------------------------------
        fee, _ = FeeStructure.objects.get_or_create(
            name="Scolarité — 1ère tranche (2025-2026)",
            classroom=None,
            defaults={"amount": 75000, "due_date": date(2025, 10, 15), "academic_year": "2025-2026"},
        )
        methods = ["CASH", "ORANGE_MONEY", "WAVE", "MTN_MOMO"]
        receipt_idx = 0
        for student in Student.objects.all()[:12]:
            receipt_idx += 1
            StudentPayment.objects.get_or_create(
                receipt_number=f"REC-2025-{receipt_idx:04d}",
                defaults={
                    "student": student, "fee_structure": fee,
                    "amount_paid": 75000,
                    "payment_method": random.choice(methods),
                },
            )
        self.stdout.write(f"  [OK] {receipt_idx} paiements enregistrés")

        # ------------------------------------------------------------------
        # 8. Comptes d'accès
        # ------------------------------------------------------------------
        admin, created = User.objects.get_or_create(
            email="admin@ecole.africa",
            defaults={
                "username": "admin", "first_name": "Amadou", "last_name": "DIOP",
                "role": "ADMIN", "is_staff": True, "is_superuser": False,
                "phone": "+237 6 99 00 00 00",
            },
        )
        admin.is_superuser = False  # interface ÉCOLE uniquement (séparation stricte)
        admin.set_password("admin123")
        admin.save()

        platform_admin, _ = User.objects.get_or_create(
            email="plateforme@gestion-ecole.ml",
            defaults={
                "username": "plateforme", "first_name": "Super", "last_name": "Admin",
                "role": "ADMIN", "is_staff": True, "is_superuser": True,
                "school": None,
            },
        )
        platform_admin.is_superuser = True  # interface PLATEFORME uniquement
        platform_admin.school = None
        platform_admin.set_password("plateforme123")
        platform_admin.save()

        comptable_user, _ = User.objects.get_or_create(
            email="comptable@ecole.africa",
            defaults={
                "username": "comptable", "first_name": "Bineta", "last_name": "NDIAYE",
                "role": "COMPTABLE", "phone": "+237 6 77 88 99 00",
            },
        )
        comptable_user.set_password("compta123")
        comptable_user.save()

        parent_user, _ = User.objects.get_or_create(
            email="parent@ecole.africa",
            defaults={
                "username": "parent", "first_name": "Fatou", "last_name": "DIALLO",
                "role": "PARENT", "phone": "+237 6 55 44 33 22",
            },
        )
        parent_user.set_password("parent123")
        parent_user.save()

        # ------------------------------------------------------------------
        # 5. Isolation multi-écoles : tout rattacher à l'école de la démo
        # ------------------------------------------------------------------
        from accounts.models import School as PlatformSchool
        from school_settings.models import SchoolSetting as SchoolSettingModel

        setting = SchoolSettingModel.objects.first()
        demo_school, created = PlatformSchool.objects.get_or_create(
            name=(setting.school_name if setting and setting.school_name else "École Démo"),
            defaults={"address": (setting.address if setting else "") or "",
                      "phone": (setting.phone if setting else "") or "",
                      "email": (setting.email if setting else "") or ""},
        )
        MODELS = [
            ("students.models", "Student"), ("teachers.models", "Teacher"),
            ("classes.models", "Class"), ("parents.models", "Parent"),
            ("courses.models", "Program"), ("courses.models", "Subject"),
            ("grades.models", "AcademicYear"), ("grades.models", "Period"),
            ("timetable.models", "Classroom"),
            ("school_calendar.models", "EventCategory"),
            ("school_calendar.models", "AcademicEvent"),
            ("admissions.models", "AdmissionApplication"),
            ("documents.models", "DocumentModele"),
        ]
        import importlib as _il
        for mod_name, cls_name in MODELS:
            model = getattr(_il.import_module(mod_name), cls_name)
            updated = model.objects.filter(school__isnull=True).update(school=demo_school)
            if updated:
                self.stdout.write(f"  [OK] {cls_name}: {updated} rattache(s) a l'ecole")

        n_users = User.objects.filter(school__isnull=True).update(school=demo_school)
        if n_users:
            self.stdout.write(f"  [OK] Users: {n_users} rattache(s) a l'ecole")

        if setting and setting.school_id is None:
            setting.school = demo_school
            setting.save()

        # ------------------------------------------------------------------
        # 6. Plateforme : abonnements, profils (sexe/région), visites démo
        # ------------------------------------------------------------------
        from datetime import timedelta as _td

        from django.utils import timezone as _tz

        from accounts.models import PlatformSetting, SubscriptionPlan

        gratuit, _ = SubscriptionPlan.objects.get_or_create(
            name="Gratuit",
            defaults={"price": 0, "duration_days": 30, "max_students": 100,
                      "description": "Pour découvrir la plateforme.",
                      "features": "1 classe\nJusqu'à 100 élèves\nBulletins PDF"},
        )
        standard, _ = SubscriptionPlan.objects.get_or_create(
            name="Standard",
            defaults={"price": 15000, "duration_days": 30,
                      "description": "Pour les écoles en croissance.",
                      "features": "Classes illimitées\nComptabilité complète\nEmplois du temps\nDocuments officiels"},
        )
        premium, _ = SubscriptionPlan.objects.get_or_create(
            name="Premium",
            defaults={"price": 35000, "duration_days": 30,
                      "description": "Établissements exigeants.",
                      "features": "Tout le Standard\nAnalytique avancée\nSupport prioritaire\nSauvegardes automatiques"},
        )
        self.stdout.write("  [OK] 3 abonnements (Gratuit / Standard / Premium)")

        platform_setting = PlatformSetting.load()
        if platform_setting.default_plan is None:
            platform_setting.default_plan = standard
            platform_setting.support_email = "support@gestion-ecole.ml"
            platform_setting.save()

        if demo_school.subscription is None:
            demo_school.subscription = standard
            demo_school.subscription_until = _tz.localdate() + _td(days=90)
            demo_school.save(update_fields=['subscription', 'subscription_until'])

        # Sexe / région des comptes (pour l'analytique)
        GENDERS = ['F', 'M', 'M', 'F', 'M', 'F']
        REGIONS = ['Bamako', 'Bamako', 'Sikasso', 'Ségou', 'Kayes', 'Koulikoro',
                   'Mopti', 'Bamako', 'Sikasso', 'Gao']
        for i, user in enumerate(User.objects.all()):
            changed = []
            if not user.gender:
                user.gender = GENDERS[i % len(GENDERS)]; changed.append('gender')
            if not user.region:
                user.region = REGIONS[i % len(REGIONS)]; changed.append('region')
            if changed:
                user.save(update_fields=changed)
        self.stdout.write("  [OK] profils visiteurs (sexe / région)")

        # Historique de visites (14 jours) pour la page Analytique
        from analytics.models import VisitLog

        PATHS = ['/dashboard/', '/students/', '/accounting/', '/grades/',
                 '/courses/', '/timetable/', '/documents/', '/calendar/list/']
        users_list = list(User.objects.all())
        created_visits = 0
        for offset in range(14):
            day = _tz.localdate() - _td(days=offset)
            for idx, user in enumerate(users_list):
                # rythme variable mais déterministe
                nb_paths = (idx + offset) % 3 + 1
                for p in range(nb_paths):
                    _, was_created = VisitLog.objects.get_or_create(
                        user=user, day=day, path=PATHS[(idx * 2 + p) % len(PATHS)],
                        defaults={'ip_address': '127.0.0.1', 'user_agent': 'seed'},
                    )
                    created_visits += 1 if was_created else 0
        self.stdout.write(f"  [OK] visites de démonstration ({created_visits} lignes)")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 58))
        self.stdout.write(self.style.SUCCESS("DONNÉES DE DÉMO CRÉÉES — Comptes d'accès :"))
        self.stdout.write(self.style.SUCCESS("  École   : admin@ecole.africa / admin123 (interface école)"))
        self.stdout.write(self.style.SUCCESS("  Plateforme : plateforme@gestion-ecole.ml / plateforme123 (Super Admin)"))
        self.stdout.write(self.style.SUCCESS("  Compta  : comptable@ecole.africa / compta123"))
        self.stdout.write(self.style.SUCCESS("  Parent  : parent@ecole.africa / parent123"))
        self.stdout.write(self.style.SUCCESS("  Prof    : awa.diallo@cpbr-cm.edu / prof123"))
        self.stdout.write(self.style.SUCCESS("=" * 58))

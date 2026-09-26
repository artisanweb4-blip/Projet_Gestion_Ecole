import os
import sys
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_config.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import User
from students.models import ClassRoom, StudentProfile
from teachers.models import TeacherProfile
from courses.models import Course, Enrollment
from trs.models import Semester, ClassroomRoom, TimeSlot, Schedule
from assignments.models import Assignment, AssignmentSubmission
from exams.models import Exam, Question, ExamResult
from attendance.models import AttendanceRecord
from finance.models import FeeStructure, StudentPayment
from admissions.models import AdmissionApplication
from datetime import date, time, datetime, timedelta

def seed_database():
    print("[+] Debut du peuplement de la base de donnees avec des donnees africaines realistes...")

    # 1. Superutilisateur & Administrateur
    admin_user, created = User.objects.get_or_create(
        email="admin@ecole.africa",
        defaults={
            "username": "admin",
            "first_name": "Amadou",
            "last_name": "DIOP",
            "phone": "+221 77 123 45 67",
            "role": "ADMIN",
            "is_staff": True,
            "is_superuser": True
        }
    )
    if created:
        admin_user.set_password("admin123")
        admin_user.save()
        print("  [OK] Compte Administrateur cree (admin@ecole.africa / admin123)")
    
    # 2. Classes / Promotions
    classroom_l3, _ = ClassRoom.objects.get_or_create(
        code="L3-INFO",
        defaults={"name": "Licence 3 Informatique", "level": "Licence 3", "academic_year": "2025-2026", "capacity": 45}
    )
    classroom_m1, _ = ClassRoom.objects.get_or_create(
        code="M1-FIN",
        defaults={"name": "Master 1 Finance & Comptabilite", "level": "Master 1", "academic_year": "2025-2026", "capacity": 35}
    )
    print("  [OK] Classes creees (L3 Informatique, M1 Finance)")

    # 3. Enseignants
    teacher_user, _ = User.objects.get_or_create(
        email="ousmane.kane@ecole.africa",
        defaults={
            "username": "okane",
            "first_name": "Ousmane",
            "last_name": "KANE",
            "phone": "+225 07 88 99 00",
            "role": "TEACHER"
        }
    )
    teacher_user.set_password("teacher123")
    teacher_user.save()

    teacher_profile, _ = TeacherProfile.objects.get_or_create(
        user=teacher_user,
        defaults={"employee_id": "TCH-2026-001", "specialty": "Genie Logiciel & Bases de Donnees"}
    )
    print("  [OK] Enseignant cree (Prof. Ousmane KANE)")

    # 4. Eleves / Etudiants
    students_data = [
        ("awa.bamba@ecole.africa", "abamba", "Awa", "BAMBA", "STD-2026-001", classroom_l3),
        ("koffi.kouassi@ecole.africa", "kkouassi", "Koffi", "KOUASSI", "STD-2026-002", classroom_l3),
        ("fatoumata.traore@ecole.africa", "ftraore", "Fatoumata", "TRAORE", "STD-2026-003", classroom_m1),
    ]

    student_profiles = []
    for email, username, first_name, last_name, student_num, cls in students_data:
        u, _ = User.objects.get_or_create(
            email=email,
            defaults={"username": username, "first_name": first_name, "last_name": last_name, "role": "STUDENT"}
        )
        u.set_password("student123")
        u.save()

        sp, _ = StudentProfile.objects.get_or_create(
            user=u,
            defaults={"student_number": student_num, "classroom": cls, "gender": "F" if "a" in first_name.lower() else "M"}
        )
        student_profiles.append(sp)

    print("  [OK] Etudiants mecrees (Awa BAMBA, Koffi KOUASSI, Fatoumata TRAORE)")

    # 5. Cours
    course_algo, _ = Course.objects.get_or_create(
        code="INF101",
        defaults={
            "name": "Algorithmique & Structuration de Donnees",
            "description": "Bases de la logique algorithmique",
            "credits": 4,
            "coefficient": 3.0,
            "teacher": teacher_profile,
            "classroom": classroom_l3
        }
    )
    course_db, _ = Course.objects.get_or_create(
        code="INF202",
        defaults={
            "name": "Bases de Donnees Relationnelles & SQL",
            "description": "Conception et requetage PostgreSQL",
            "credits": 5,
            "coefficient": 4.0,
            "teacher": teacher_profile,
            "classroom": classroom_l3
        }
    )
    print("  [OK] Cours mecrees (INF101 - Algorithmique, INF202 - Bases de donnees)")

    # 6. Inscriptions
    for sp in student_profiles:
        Enrollment.objects.get_or_create(student=sp, course=course_algo)
        Enrollment.objects.get_or_create(student=sp, course=course_db)

    # 7. Salles et Creneaux Horaires
    room_nkomo, _ = ClassroomRoom.objects.get_or_create(code="AMPHI-NKOMO", defaults={"name": "Amphitheatre Kwame Nkrumah", "capacity": 150})
    slot_monday, _ = TimeSlot.objects.get_or_create(day=1, start_time=time(8, 0), end_time=time(10, 0))
    slot_tuesday, _ = TimeSlot.objects.get_or_create(day=2, start_time=time(10, 15), end_time=time(12, 15))
    sem1, _ = Semester.objects.get_or_create(name="Semestre 1", start_date=date(2025, 10, 1), end_date=date(2026, 2, 28))

    Schedule.objects.get_or_create(course=course_algo, room=room_nkomo, time_slot=slot_monday, semester=sem1)
    Schedule.objects.get_or_create(course=course_db, room=room_nkomo, time_slot=slot_tuesday, semester=sem1)
    print("  [OK] Emploi du temps planifie sans chevauchement")

    # 8. Examens & Notes
    exam1, _ = Exam.objects.get_or_create(
        title="Examen Partiel SQL",
        course=course_db,
        defaults={"exam_type": "PARTIAL", "date": datetime.now() + timedelta(days=5), "duration_minutes": 120, "total_points": 20.0}
    )

    ExamResult.objects.get_or_create(exam=exam1, student=student_profiles[0], defaults={"score": 17.5, "remarks": "Excellente maitrise des jointures SQL"})
    ExamResult.objects.get_or_create(exam=exam1, student=student_profiles[1], defaults={"score": 14.0, "remarks": "Bon travail"})
    print("  [OK] Examens et resultats enregistres")

    # 9. Presences
    for sp in student_profiles:
        AttendanceRecord.objects.get_or_create(
            student=sp,
            course=course_db,
            date=date.today(),
            defaults={"status": "PRESENT"}
        )

    # 10. Module Financier
    fee_l3, _ = FeeStructure.objects.get_or_create(
        name="Frais de Scolarite Tranche 1",
        classroom=classroom_l3,
        defaults={"amount": 450000.0, "due_date": date(2025, 11, 15)}
    )

    StudentPayment.objects.get_or_create(
        receipt_number="REC-2026-0001",
        defaults={
            "student": student_profiles[0],
            "fee_structure": fee_l3,
            "amount_paid": 450000.0,
            "payment_method": "ORANGE_MONEY",
            "is_receipt_issued": True
        }
    )
    print("  [OK] Donnees financieres et paiements Mobile Money initialises")

    print("\n[SUCCESS] Base de donnees initialisee avec succes ! Tous les modules sont prets pour la production.")

if __name__ == '__main__':
    seed_database()

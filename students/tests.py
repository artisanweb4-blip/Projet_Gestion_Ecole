from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from students.models import ClassRoom, StudentProfile
from teachers.models import TeacherProfile
from courses.models import Course
from trs.models import Semester, ClassroomRoom, TimeSlot, Schedule
from exams.models import Exam, ExamResult
from finance.models import FeeStructure, StudentPayment
from datetime import date, time, datetime

User = get_user_model()

class BusinessRulesTestCase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin@test.com", "admin", "pass123")
        self.teacher_user = User.objects.create_user("teacher@test.com", "teacher", "pass123", role="TEACHER")
        self.student_user = User.objects.create_user("student@test.com", "student", "pass123", role="STUDENT")

        self.classroom = ClassRoom.objects.create(code="L3-INFO", name="Licence 3 Informatique")
        self.teacher = TeacherProfile.objects.create(user=self.teacher_user, employee_id="TCH-001", specialty="Informatique")
        self.student = StudentProfile.objects.create(user=self.student_user, student_number="STD-001", classroom=self.classroom)

        self.course = Course.objects.create(code="INF101", name="Algorithmique", teacher=self.teacher, classroom=self.classroom)

    def test_exam_score_range_validation(self):
        """Vérifie que les notes doivent être comprises entre 0 et total_points (20)."""
        exam = Exam.objects.create(title="Examen", course=self.course, date=datetime.now(), total_points=20.0)

        # Note invalide > 20
        with self.assertRaises(ValidationError):
            res = ExamResult(exam=exam, student=self.student, score=25.0)
            res.full_clean()

    def test_payment_receipt_deletion_locking(self):
        """Vérifie qu'un paiement ne peut pas être supprimé si le reçu a été émis."""
        fee = FeeStructure.objects.create(name="Scolarité", amount=100000.0, due_date=date.today())
        payment = StudentPayment.objects.create(
            student=self.student,
            fee_structure=fee,
            amount_paid=100000.0,
            receipt_number="REC-9999",
            is_receipt_issued=True
        )

        with self.assertRaises(ValidationError):
            payment.delete()

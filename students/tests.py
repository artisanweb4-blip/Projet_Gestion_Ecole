from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from classes.models import Class
from courses.models import Course, Program, Subject
from exams.models import Exam, ExamResult
from students.models import Student
from teachers.models import Teacher

User = get_user_model()


class BusinessRulesTestCase(TestCase):
    """Tests des règles métier (notes, reçus, matricules)."""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@test.com", username="admin",
            first_name="Admin", last_name="GCE", password="pass123",
        )
        self.teacher_user = User.objects.create_user(
            email="teacher@test.com", username="teacher",
            first_name="Prof", last_name="Test", password="pass123", role="TEACHER",
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user, first_name="Prof", last_name="Test",
            employee_id="TCH-001", specialization="Informatique",
            hire_date=date(2020, 9, 1), phone="+237600000000",
        )
        self.program = Program.objects.create(code="COL", name="Collège")
        self.klass = Class.objects.create(name="6ème A", level="6ème", program=self.program)
        self.student = Student.objects.create(
            first_name="Élève", last_name="Test", gender="M",
            date_of_birth=date(2012, 1, 1), place_of_birth="Yaoundé",
            address="Yaoundé", phone="+237600000001",
            emergency_contact_name="Parent", emergency_contact_phone="+237600000002",
            class_group=self.klass,
        )
        self.subject = Subject.objects.create(name="Algorithmique", code="ALGO")
        self.course = Course.objects.create(
            name="Algorithmique", subject=self.subject,
            school_class=self.klass, teacher=self.teacher,
        )

    def test_matricule_auto_generated(self):
        self.assertTrue(self.student.student_id.startswith("STD-"))
        self.assertIsNotNone(self.student.qr_code)
        self.assertIsNotNone(self.student.barcode)

    def test_exam_score_range_validation(self):
        exam = Exam.objects.create(
            title="Examen", course=self.course,
            date=datetime.now(), total_points=20.0,
        )
        with self.assertRaises(ValidationError):
            ExamResult.objects.create(exam=exam, student=self.student, score=25.0)


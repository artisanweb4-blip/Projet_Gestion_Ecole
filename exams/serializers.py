from rest_framework import serializers
from .models import Exam, Question, ExamResult
from courses.serializers import CourseSerializer
from students.serializers import StudentProfileSerializer

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ('id', 'exam', 'question_type', 'text', 'points', 'options', 'created_at')


class ExamSerializer(serializers.ModelSerializer):
    course_detail = CourseSerializer(source='course', read_only=True)
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Exam
        fields = ('id', 'title', 'exam_type', 'course', 'course_detail', 'date', 'duration_minutes', 'total_points', 'questions', 'created_at')


class ExamResultSerializer(serializers.ModelSerializer):
    exam_detail = ExamSerializer(source='exam', read_only=True)
    student_detail = StudentProfileSerializer(source='student', read_only=True)

    class Meta:
        model = ExamResult
        fields = ('id', 'exam', 'exam_detail', 'student', 'student_detail', 'score', 'remarks', 'created_at')

    def validate(self, attrs):
        instance = ExamResult(**attrs)
        if self.instance:
            instance.pk = self.instance.pk
        instance.full_clean()
        return attrs

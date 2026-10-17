from rest_framework import serializers

from students.serializers import StudentSerializer
from teachers.serializers import TeacherSerializer

from .models import Course, Enrollment


class CourseSerializer(serializers.ModelSerializer):
    teacher_detail = TeacherSerializer(source='teacher', read_only=True)
    class_detail = serializers.StringRelatedField(source='school_class', read_only=True)
    subject_detail = serializers.StringRelatedField(source='subject', read_only=True)

    class Meta:
        model = Course
        fields = ('id', 'code', 'name', 'description', 'subject', 'subject_detail',
                  'school_class', 'class_detail', 'teacher', 'teacher_detail',
                  'credits', 'coefficient', 'created_at')


class EnrollmentSerializer(serializers.ModelSerializer):
    student_detail = StudentSerializer(source='student', read_only=True)
    course_detail = CourseSerializer(source='course', read_only=True)

    class Meta:
        model = Enrollment
        fields = ('id', 'course', 'course_detail', 'student', 'student_detail', 'created_at')

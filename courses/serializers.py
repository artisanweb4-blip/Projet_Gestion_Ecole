from rest_framework import serializers
from .models import Course, Enrollment
from teachers.serializers import TeacherProfileSerializer
from students.serializers import ClassRoomSerializer, StudentProfileSerializer

class CourseSerializer(serializers.ModelSerializer):
    teacher_detail = TeacherProfileSerializer(source='teacher', read_only=True)
    classroom_detail = ClassRoomSerializer(source='classroom', read_only=True)
    enrolled_students_count = serializers.IntegerField(source='enrollments.count', read_only=True)

    class Meta:
        model = Course
        fields = ('id', 'code', 'name', 'description', 'credits', 'coefficient', 'teacher', 'teacher_detail', 'classroom', 'classroom_detail', 'enrolled_students_count', 'created_at')


class EnrollmentSerializer(serializers.ModelSerializer):
    student_detail = StudentProfileSerializer(source='student', read_only=True)
    course_detail = CourseSerializer(source='course', read_only=True)

    class Meta:
        model = Enrollment
        fields = ('id', 'student', 'student_detail', 'course', 'course_detail', 'enrollment_date', 'created_at')

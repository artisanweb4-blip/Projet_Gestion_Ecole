from rest_framework import serializers
from .models import AttendanceRecord, AbsenceJustification
from courses.serializers import CourseSerializer
from students.serializers import StudentProfileSerializer

class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_detail = StudentProfileSerializer(source='student', read_only=True)
    course_detail = CourseSerializer(source='course', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = ('id', 'student', 'student_detail', 'course', 'course_detail', 'date', 'status', 'status_display', 'remarks', 'created_at')


class AbsenceJustificationSerializer(serializers.ModelSerializer):
    student_detail = StudentProfileSerializer(source='student', read_only=True)
    attendance_record_detail = AttendanceRecordSerializer(source='attendance_record', read_only=True)

    class Meta:
        model = AbsenceJustification
        fields = ('id', 'student', 'student_detail', 'attendance_record', 'attendance_record_detail', 'reason', 'document', 'is_approved', 'created_at')

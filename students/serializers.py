from rest_framework import serializers
from .models import ClassRoom, StudentProfile
from accounts.serializers import UserSerializer

class ClassRoomSerializer(serializers.ModelSerializer):
    student_count = serializers.IntegerField(source='students.count', read_only=True)

    class Meta:
        model = ClassRoom
        fields = ('id', 'code', 'name', 'level', 'academic_year', 'capacity', 'student_count', 'created_at')


class StudentProfileSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)
    classroom_detail = ClassRoomSerializer(source='classroom', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = StudentProfile
        fields = (
            'id', 'user', 'user_detail', 'full_name', 'student_number', 
            'date_of_birth', 'gender', 'address', 'guardian_name', 
            'guardian_phone', 'guardian_email', 'parent_user', 'classroom', 
            'classroom_detail', 'created_at'
        )

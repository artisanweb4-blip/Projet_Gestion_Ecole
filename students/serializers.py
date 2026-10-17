from rest_framework import serializers

from accounts.serializers import UserSerializer
from .models import Student


class StudentSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)
    class_group_detail = serializers.StringRelatedField(source='class_group', read_only=True)
    full_name = serializers.CharField(read_only=True)
    matricule = serializers.CharField(read_only=True)

    class Meta:
        model = Student
        fields = (
            'id', 'student_id', 'matricule', 'first_name', 'last_name', 'full_name',
            'gender', 'date_of_birth', 'phone', 'email', 'class_group',
            'class_group_detail', 'user', 'user_detail', 'enrollment_date',
            'is_active', 'photo',
        )


# Alias de compatibilité avec l'ancien nom utilisé dans les autres modules
StudentProfileSerializer = StudentSerializer

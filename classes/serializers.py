from rest_framework import serializers

from .models import Class


class ClassSerializer(serializers.ModelSerializer):
    student_count = serializers.IntegerField(source='students.count', read_only=True)

    class Meta:
        model = Class
        fields = ('id', 'name', 'level', 'section', 'capacity', 'room',
                  'program', 'responsible', 'student_count', 'is_active')

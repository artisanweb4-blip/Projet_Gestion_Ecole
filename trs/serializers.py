from rest_framework import serializers
from .models import Semester, ClassroomRoom, TimeSlot, Schedule
from courses.serializers import CourseSerializer

class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = ('id', 'name', 'academic_year', 'start_date', 'end_date', 'created_at')


class ClassroomRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassroomRoom
        fields = ('id', 'code', 'name', 'building', 'capacity', 'created_at')


class TimeSlotSerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(source='get_day_display', read_only=True)

    class Meta:
        model = TimeSlot
        fields = ('id', 'day', 'day_display', 'start_time', 'end_time', 'created_at')


class ScheduleSerializer(serializers.ModelSerializer):
    course_detail = CourseSerializer(source='course', read_only=True)
    room_detail = ClassroomRoomSerializer(source='room', read_only=True)
    time_slot_detail = TimeSlotSerializer(source='time_slot', read_only=True)
    semester_detail = SemesterSerializer(source='semester', read_only=True)

    class Meta:
        model = Schedule
        fields = ('id', 'course', 'course_detail', 'room', 'room_detail', 'time_slot', 'time_slot_detail', 'semester', 'semester_detail', 'created_at')

    def validate(self, attrs):
        # Exécuter la validation métier personnalisée définies dans le modèle
        instance = Schedule(**attrs)
        if self.instance:
            instance.pk = self.instance.pk
        instance.full_clean()
        return attrs

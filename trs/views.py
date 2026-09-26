from rest_framework import viewsets, permissions
from .models import Semester, ClassroomRoom, TimeSlot, Schedule
from .serializers import SemesterSerializer, ClassroomRoomSerializer, TimeSlotSerializer, ScheduleSerializer

class SemesterViewSet(viewsets.ModelViewSet):
    queryset = Semester.objects.all().order_by('-start_date')
    serializer_class = SemesterSerializer
    permission_classes = [permissions.IsAuthenticated]


class ClassroomRoomViewSet(viewsets.ModelViewSet):
    queryset = ClassroomRoom.objects.all().order_by('code')
    serializer_class = ClassroomRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['code', 'name', 'building']


class TimeSlotViewSet(viewsets.ModelViewSet):
    queryset = TimeSlot.objects.all().order_by('day', 'start_time')
    serializer_class = TimeSlotSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['day']


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all().order_by('time_slot__day', 'time_slot__start_time')
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['course', 'room', 'semester', 'time_slot__day']

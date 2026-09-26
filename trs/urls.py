from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SemesterViewSet, ClassroomRoomViewSet, TimeSlotViewSet, ScheduleViewSet

router = DefaultRouter()
router.register(r'semesters', SemesterViewSet, basename='semester')
router.register(r'rooms', ClassroomRoomViewSet, basename='room')
router.register(r'timeslots', TimeSlotViewSet, basename='timeslot')
router.register(r'schedules', ScheduleViewSet, basename='schedule')

urlpatterns = [
    path('', include(router.urls)),
]

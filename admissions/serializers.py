from rest_framework import serializers
from .models import AdmissionApplication
from students.serializers import ClassRoomSerializer

class AdmissionApplicationSerializer(serializers.ModelSerializer):
    requested_classroom_detail = ClassRoomSerializer(source='requested_classroom', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AdmissionApplication
        fields = (
            'id', 'application_number', 'applicant_first_name', 'applicant_last_name',
            'applicant_email', 'applicant_phone', 'requested_classroom',
            'requested_classroom_detail', 'status', 'status_display', 'documents',
            'notes', 'created_at'
        )

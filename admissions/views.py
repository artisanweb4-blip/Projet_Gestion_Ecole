from rest_framework import viewsets, permissions
from .models import AdmissionApplication
from .serializers import AdmissionApplicationSerializer

class AdmissionApplicationViewSet(viewsets.ModelViewSet):
    queryset = AdmissionApplication.objects.all().order_by('-created_at')
    serializer_class = AdmissionApplicationSerializer
    filterset_fields = ['status', 'requested_classroom']
    search_fields = ['application_number', 'applicant_first_name', 'applicant_last_name', 'applicant_email']

    def get_queryset(self):
        # Isolation multi-écoles : évalué par requête (gestionnaire filtrant)
        return AdmissionApplication.objects.all().order_by('-created_at')
    def get_permissions(self):
        # Permet la soumission publique d'un dossier de candidature (POST), mais restreint la consultation
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

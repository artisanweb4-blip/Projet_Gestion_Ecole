from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from .models import FeeStructure, StudentPayment
from .serializers import FeeStructureSerializer, StudentPaymentSerializer
from core.permissions import IsAdminUserRole

class FeeStructureViewSet(viewsets.ModelViewSet):
    queryset = FeeStructure.objects.all().order_by('-due_date')
    serializer_class = FeeStructureSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['classroom', 'academic_year']

    def get_queryset(self):
        # Isolation multi-écoles : évalué par requête (gestionnaire filtrant)
        return FeeStructure.objects.all().order_by('-due_date')


class StudentPaymentViewSet(viewsets.ModelViewSet):
    queryset = StudentPayment.objects.all().order_by('-payment_date')
    serializer_class = StudentPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['student', 'fee_structure', 'payment_method', 'is_receipt_issued']
    search_fields = ['receipt_number', 'student__user__first_name', 'student__user__last_name']

    def get_queryset(self):
        # Isolation multi-écoles : évalué par requête (gestionnaire filtrant)
        return StudentPayment.objects.all().order_by('-payment_date')
    def destroy(self, request, *args, **kwargs):
        """Intercepteur pour appliquer le verrouillage des reçus lors de la suppression."""
        instance = self.get_object()
        if instance.is_receipt_issued:
            return Response(
                {"error": "Impossible de supprimer un paiement dont le reçu officiel a déjà été émis."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='reports', permission_classes=[IsAdminUserRole])
    def financial_report(self, request):
        """
        Rapport financier global (Total encaissements, ventilation par mode de paiement).
        """
        total_collected = StudentPayment.objects.aggregate(total=Sum('amount_paid'))['total'] or 0
        payments_by_method = StudentPayment.objects.values('payment_method').annotate(total=Sum('amount_paid'))

        report_data = {
            'total_revenue': total_collected,
            'payment_method_breakdown': payments_by_method,
            'currency': 'FCFA'
        }
        return Response(report_data, status=status.HTTP_200_OK)

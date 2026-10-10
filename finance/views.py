from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from .models import StudentPayment
from .serializers import StudentPaymentSerializer
from core.permissions import IsAdminUserRole


class StudentPaymentViewSet(viewsets.ModelViewSet):
    queryset = StudentPayment.objects.all().order_by('-payment_date')
    serializer_class = StudentPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['student', 'payment_method', 'is_receipt_issued', 'periodicity']
    search_fields = ['receipt_number', 'student__first_name', 'student__last_name']

    def get_queryset(self):
        # Isolation multi-écoles : évalué par requête (gestionnaire filtrant)
        return StudentPayment.objects.all().order_by('-payment_date')

    @action(detail=False, methods=['get'], url_path='reports', permission_classes=[IsAdminUserRole])
    def financial_report(self, request):
        """Rapport financier global (Total encaissements, ventilation par mode)."""
        total_collected = StudentPayment.objects.aggregate(total=Sum('amount_paid'))['total'] or 0
        payments_by_method = StudentPayment.objects.values('payment_method').annotate(total=Sum('amount_paid'))

        report_data = {
            'total_revenue': total_collected,
            'payment_method_breakdown': payments_by_method,
            'currency': 'FCFA'
        }
        return Response(report_data, status=status.HTTP_200_OK)

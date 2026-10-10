from rest_framework import serializers
from .models import StudentPayment
from students.serializers import StudentSerializer as StudentProfileSerializer


class StudentPaymentSerializer(serializers.ModelSerializer):
    student_detail = StudentProfileSerializer(source='student', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    periodicity_display = serializers.CharField(source='get_periodicity_display', read_only=True)

    class Meta:
        model = StudentPayment
        fields = ('id', 'student', 'student_detail', 'school', 'periodicity',
                  'periodicity_display', 'period_label', 'amount_paid',
                  'payment_date', 'payment_method', 'payment_method_display',
                  'receipt_number', 'is_receipt_issued', 'created_at')

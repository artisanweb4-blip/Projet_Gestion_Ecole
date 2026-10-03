from rest_framework import serializers
from .models import FeeStructure, StudentPayment
from classes.serializers import ClassSerializer as ClassRoomSerializer
from students.serializers import StudentSerializer as StudentProfileSerializer

class FeeStructureSerializer(serializers.ModelSerializer):
    classroom_detail = ClassRoomSerializer(source='classroom', read_only=True)

    class Meta:
        model = FeeStructure
        fields = ('id', 'name', 'classroom', 'classroom_detail', 'amount', 'due_date', 'academic_year', 'created_at')


class StudentPaymentSerializer(serializers.ModelSerializer):
    student_detail = StudentProfileSerializer(source='student', read_only=True)
    fee_structure_detail = FeeStructureSerializer(source='fee_structure', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = StudentPayment
        fields = ('id', 'student', 'student_detail', 'fee_structure', 'fee_structure_detail', 'amount_paid', 'payment_date', 'payment_method', 'payment_method_display', 'receipt_number', 'is_receipt_issued', 'created_at')

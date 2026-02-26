# students/serializers.py
from rest_framework import serializers
from .models import Student, Parent, Invoice, Payment


class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = ['id', 'phone_number', 'full_name']


class StudentSerializer(serializers.ModelSerializer):
    parent = ParentSerializer(read_only=True)
    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=Parent.objects.all(), source='parent', write_only=True
    )

    class Meta:
        model = Student
        fields = [
            'id', 'first_name', 'last_name', 'dob', 'gender', 'blood_group',
            'phone_number', 'address', 'emergency_contact',
            'parent', 'parent_id', 'class_teacher', 'class_name', 'active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class InvoiceSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source='student', write_only=True
    )

    class Meta:
        model = Invoice
        fields = ['id', 'student', 'student_id', 'month', 'amount', 'due_date', 'is_paid']
        read_only_fields = ['is_paid']


class PaymentSerializer(serializers.ModelSerializer):
    invoice = InvoiceSerializer(read_only=True)
    invoice_id = serializers.PrimaryKeyRelatedField(
        queryset=Invoice.objects.all(), source='invoice', write_only=True
    )
    paid_by = serializers.StringRelatedField(read_only=True)  # show user who paid

    class Meta:
        model = Payment
        fields = ['id', 'invoice', 'invoice_id', 'amount', 'paid_at', 'paid_by']
        read_only_fields = ['paid_at', 'paid_by']

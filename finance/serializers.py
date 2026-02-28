from rest_framework import serializers

from .models import Bonus, Deduction, Invoice, Payment, Payroll


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['paid_by', 'paid_at']


class PayrollSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.full_name', read_only=True)

    class Meta:
        model = Payroll
        fields = [
            'id',
            'employee',
            'employee_name',
            'month',
            'base_salary',
            'total_present_days',
            'overtime_amount',
            'total_bonus',
            'total_deductions',
            'net_salary',
            'status',
            'created_at',
        ]
        read_only_fields = [
            'base_salary',
            'total_present_days',
            'total_bonus',
            'total_deductions',
            'net_salary',
            'created_at',
            'status',
        ]


class PayrollGenerateSerializer(serializers.Serializer):
    month = serializers.CharField(required=True)
    employee_id = serializers.IntegerField(required=False)
    overtime_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)


class BonusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bonus
        fields = '__all__'


class DeductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deduction
        fields = '__all__'

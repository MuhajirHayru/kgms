from rest_framework import serializers

from .models import (
    Bonus,
    CreditRepayment,
    CreditRequest,
    DashboardNotification,
    Deduction,
    ExpenseRequest,
    Invoice,
    LedgerEntry,
    Payment,
    Payroll,
    PayrollSetting,
    SchoolAccount,
)


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
    requested_by_name = serializers.CharField(source='requested_by.full_name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.full_name', read_only=True)

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
            'gross_salary',
            'tax_rate_percent',
            'tax_amount',
            'net_salary',
            'status',
            'requested_by',
            'requested_by_name',
            'requested_at',
            'reviewed_by',
            'reviewed_by_name',
            'reviewed_at',
            'review_comment',
            'created_at',
        ]
        read_only_fields = [
            'base_salary',
            'total_present_days',
            'total_bonus',
            'total_deductions',
            'gross_salary',
            'tax_rate_percent',
            'tax_amount',
            'net_salary',
            'created_at',
            'status',
            'requested_by',
            'requested_by_name',
            'requested_at',
            'reviewed_by',
            'reviewed_by_name',
            'reviewed_at',
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


class PayrollSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollSetting
        fields = ['id', 'tax_rate_percent', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class EmployeeSalaryUpdateSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField(required=True)
    salary = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)


class PayrollRequestSerializer(serializers.Serializer):
    payroll_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=True,
        allow_empty=False,
    )


class PayrollReviewSerializer(serializers.Serializer):
    approve = serializers.BooleanField(required=True)
    comment = serializers.CharField(required=False, allow_blank=True)


class DashboardNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardNotification
        fields = [
            'id',
            'category',
            'title',
            'message',
            'is_read',
            'is_hidden',
            'created_at',
        ]
        read_only_fields = fields


class HideNotificationsSerializer(serializers.Serializer):
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
        default=list,
    )
    hide_all = serializers.BooleanField(required=False, default=False)


class SchoolAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolAccount
        fields = ['id', 'current_balance', 'is_initialized', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class InitializeSchoolAccountSerializer(serializers.Serializer):
    initial_balance = serializers.DecimalField(max_digits=14, decimal_places=2)


class LedgerEntrySerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)

    class Meta:
        model = LedgerEntry
        fields = [
            'id',
            'entry_type',
            'amount_delta',
            'description',
            'created_by',
            'created_by_name',
            'created_at',
        ]
        read_only_fields = fields


class ManualIncomeSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    description = serializers.CharField(required=False, allow_blank=True)


class ExpenseRequestSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.CharField(source='requested_by.full_name', read_only=True)

    class Meta:
        model = ExpenseRequest
        fields = [
            'id',
            'requested_by',
            'requested_by_name',
            'category',
            'title',
            'amount',
            'reason',
            'status',
            'admin_comment',
            'reviewed_by',
            'reviewed_at',
            'paid_by',
            'paid_at',
            'created_at',
        ]
        read_only_fields = [
            'requested_by', 'status', 'admin_comment', 'reviewed_by', 'reviewed_at',
            'paid_by', 'paid_at', 'created_at'
        ]


class ExpenseReviewSerializer(serializers.Serializer):
    approve = serializers.BooleanField(required=True)
    comment = serializers.CharField(required=False, allow_blank=True)


class CreditRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.full_name', read_only=True)

    class Meta:
        model = CreditRequest
        fields = [
            'id',
            'employee',
            'employee_name',
            'amount',
            'reason',
            'status',
            'admin_comment',
            'reviewed_by',
            'reviewed_at',
            'given_by',
            'given_at',
            'total_repaid',
            'created_at',
        ]
        read_only_fields = [
            'status', 'admin_comment', 'reviewed_by', 'reviewed_at',
            'given_by', 'given_at', 'total_repaid', 'created_at'
        ]


class CreditReviewSerializer(serializers.Serializer):
    approve = serializers.BooleanField(required=True)
    comment = serializers.CharField(required=False, allow_blank=True)


class CreditRepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditRepayment
        fields = ['id', 'credit_request', 'amount', 'recorded_by', 'created_at']
        read_only_fields = ['recorded_by', 'created_at']


class MonthlyReportSerializer(serializers.Serializer):
    month = serializers.CharField()
    total_income = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_expense = serializers.DecimalField(max_digits=14, decimal_places=2)
    profit = serializers.DecimalField(max_digits=14, decimal_places=2)
    entries = LedgerEntrySerializer(many=True)

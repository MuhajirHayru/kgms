# students/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import (
    Invoice,
    Parent,
    ParentNotification,
    Payment,
    PenaltySetting,
    Student,
    StudentCertificate,
)


class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = ['id', 'phone_number', 'full_name']


class StudentSerializer(serializers.ModelSerializer):
    dob = serializers.DateField(input_formats=["%d-%m-%Y", "%Y-%m-%d"])
    transport = serializers.ChoiceField(choices=Student._meta.get_field("transport").choices, required=True)
    parent = ParentSerializer(read_only=True)
    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=Parent.objects.all(), source='parent', write_only=True
    )
    certificates = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    certificate_files = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Student
        fields = [
            'id', 'first_name', 'last_name', 'dob', 'gender',
            'transport', 'address', 'emergency_contact',
            'parent', 'parent_id', 'class_teacher', 'class_name', 'active',
            'student_photo', 'certificates', 'certificate_files', 'monthly_tuition_fee',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'certificate_files']
        extra_kwargs = {
            'student_photo': {'required': False, 'allow_null': True},
        }

    def validate(self, attrs):
        transport = attrs.get("transport")
        address = (attrs.get("address") or "").strip()
        if transport == "BUS" and not address:
            raise serializers.ValidationError(
                {"address": ["Address is required when transport is BUS."]}
            )
        return attrs

    def get_certificate_files(self, obj):
        request = self.context.get("request")
        files = []
        for certificate in obj.certificates.all():
            if request is not None:
                files.append(request.build_absolute_uri(certificate.file.url))
            else:
                files.append(certificate.file.url)
        return files

    def create(self, validated_data):
        certificate_files = validated_data.pop("certificates", [])
        student = super().create(validated_data)
        for file_obj in certificate_files:
            StudentCertificate.objects.create(student=student, file=file_obj)
        return student


class InvoiceSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source='student', write_only=True
    )
    total_amount_due = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    passed_days = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'student', 'student_id', 'month', 'amount', 'due_date',
            'is_paid', 'penalty_amount', 'total_amount_due', 'passed_days'
        ]
        read_only_fields = ['is_paid', 'penalty_amount', 'total_amount_due', 'passed_days']

    def get_passed_days(self, obj):
        if obj.is_paid:
            return 0
        today = timezone.localdate()
        if obj.due_date >= today:
            return 0
        return (today - obj.due_date).days


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


class PenaltySettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PenaltySetting
        fields = ['id', 'penalty_per_day', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ParentNotificationSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ParentNotification
        fields = [
            'id', 'notification_type', 'title', 'message',
            'student', 'student_name', 'invoice', 'sent_at'
        ]
        read_only_fields = fields

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"


class AccountantDashboardSerializer(serializers.Serializer):
    month = serializers.CharField()
    total_students = serializers.IntegerField()
    paid_students = serializers.IntegerField()
    unpaid_students = serializers.IntegerField()
    overdue_students = serializers.IntegerField()
    paid_invoices = InvoiceSerializer(many=True)
    unpaid_invoices = InvoiceSerializer(many=True)

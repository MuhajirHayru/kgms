# students/serializers.py
from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from .models import (
    Invoice,
    Parent,
    ParentNotification,
    Payment,
    PenaltySetting,
    Student,
    StudentCertificate,
    StudentFeeSetting,
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
            'id', 'first_name', 'last_name', 'dob', 'gender', 'category', 'grade_level',
            'transport', 'address', 'emergency_contact',
            'parent', 'parent_id', 'class_teacher', 'class_name', 'active',
            'student_photo', 'certificates', 'certificate_files', 'monthly_tuition_fee',
            'registration_fee', 'transport_fee',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'certificate_files',
            'monthly_tuition_fee', 'registration_fee', 'transport_fee', 'class_name',
        ]
        extra_kwargs = {
            'student_photo': {'required': False, 'allow_null': True},
        }

    def validate(self, attrs):
        category = attrs.get("category", getattr(self.instance, "category", None))
        grade_level = attrs.get("grade_level", getattr(self.instance, "grade_level", None))
        transport = attrs.get("transport", getattr(self.instance, "transport", None))
        address = (attrs.get("address") or "").strip()

        kg_grades = {"KG1", "KG2", "KG3"}
        elementary_grades = {
            "GRADE1", "GRADE2", "GRADE3", "GRADE4",
            "GRADE5", "GRADE6", "GRADE7", "GRADE8",
        }

        if category == "KG" and grade_level not in kg_grades:
            raise serializers.ValidationError(
                {"grade_level": ["KG students must use KG1, KG2, or KG3."]}
            )

        if category == "ELEMENTARY" and grade_level not in elementary_grades:
            raise serializers.ValidationError(
                {"grade_level": ["Elementary students must use Grade 1 to Grade 8."]}
            )

        if transport == "BUS" and not address:
            raise serializers.ValidationError(
                {"address": ["Address is required when transport is BUS."]}
            )
        return attrs

    def _get_monthly_fee(self, category, fee_setting):
        if category == "KG":
            return fee_setting.kg_monthly_fee
        return fee_setting.elementary_monthly_fee

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
        fee_setting = StudentFeeSetting.get_current()
        category = validated_data["category"]
        transport = validated_data["transport"]
        validated_data["class_name"] = validated_data["grade_level"]
        validated_data["monthly_tuition_fee"] = self._get_monthly_fee(category, fee_setting)
        validated_data["registration_fee"] = fee_setting.registration_fee
        validated_data["transport_fee"] = (
            fee_setting.bus_transport_fee if transport == "BUS" else 0
        )

        request = self.context.get("request")
        created_by = None
        if request is not None and getattr(request.user, "is_authenticated", False):
            created_by = request.user

        with transaction.atomic():
            student = super().create(validated_data)
            for file_obj in certificate_files:
                StudentCertificate.objects.create(student=student, file=file_obj)

            from finance.services import record_account_transaction

            student_name = f"{student.first_name} {student.last_name}".strip()
            if student.registration_fee > 0:
                record_account_transaction(
                    amount_delta=student.registration_fee,
                    entry_type="REGISTRATION_FEE",
                    description=f"Registration fee received for {student_name} ({student.category}).",
                    created_by=created_by,
                )

            if student.transport_fee > 0:
                record_account_transaction(
                    amount_delta=student.transport_fee,
                    entry_type="TRANSPORT_FEE",
                    description=f"Transport fee received for {student_name} (BUS).",
                    created_by=created_by,
                )

            if student.monthly_tuition_fee > 0:
                month = timezone.localdate().strftime("%Y-%m")
                invoice = Invoice.objects.create(
                    student=student,
                    month=month,
                    amount=student.monthly_tuition_fee,
                    due_date=timezone.localdate(),
                    is_paid=True,
                )
                Payment.objects.create(
                    invoice=invoice,
                    amount=student.monthly_tuition_fee,
                    paid_by=created_by,
                )
                record_account_transaction(
                    amount_delta=student.monthly_tuition_fee,
                    entry_type="MONTHLY_FEE",
                    description=f"Monthly fee received for {student_name} ({month}).",
                    created_by=created_by,
                )

        return student

    def update(self, instance, validated_data):
        category = validated_data.get("category", instance.category)
        transport = validated_data.get("transport", instance.transport)
        validated_data["class_name"] = validated_data.get("grade_level", instance.grade_level)
        fee_setting = StudentFeeSetting.get_current()
        validated_data["monthly_tuition_fee"] = self._get_monthly_fee(category, fee_setting)
        validated_data["registration_fee"] = fee_setting.registration_fee
        validated_data["transport_fee"] = (
            fee_setting.bus_transport_fee if transport == "BUS" else 0
        )
        return super().update(instance, validated_data)


class InvoiceSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source='student', write_only=True
    )
    total_amount_due = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    passed_days = serializers.SerializerMethodField(read_only=True)
    payment_status = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'student', 'student_id', 'month', 'amount', 'due_date',
            'is_paid', 'penalty_amount', 'total_amount_due', 'passed_days', 'payment_status'
        ]
        read_only_fields = ['is_paid', 'penalty_amount', 'total_amount_due', 'passed_days', 'payment_status']

    def get_passed_days(self, obj):
        if obj.is_paid:
            return 0
        today = timezone.localdate()
        if obj.due_date >= today:
            return 0
        return (today - obj.due_date).days

    def get_payment_status(self, obj):
        if obj.is_paid:
            return "PAID"
        today = timezone.localdate()
        if obj.due_date < today:
            return "OVERDUE"
        return "PENDING"


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


class StudentFeeSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentFeeSetting
        fields = [
            'id',
            'kg_monthly_fee',
            'elementary_monthly_fee',
            'registration_fee',
            'bus_transport_fee',
            'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']


class StudentGradeGroupSerializer(serializers.Serializer):
    grade_level = serializers.CharField()
    total_students = serializers.IntegerField()
    students = StudentSerializer(many=True)


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


class AccountantMonthlyListSerializer(serializers.Serializer):
    month = serializers.CharField()
    total_students = serializers.IntegerField()
    paid_students = serializers.IntegerField()
    unpaid_students = serializers.IntegerField()
    overdue_students = serializers.IntegerField()
    unpaid_invoices = InvoiceSerializer(many=True)

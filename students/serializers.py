# students/serializers.py
from rest_framework import serializers
from .models import Student, Parent, Invoice, Payment, StudentCertificate


class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = ['id', 'phone_number', 'full_name']


class StudentSerializer(serializers.ModelSerializer):
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
            'phone_number', 'address', 'emergency_contact',
            'parent', 'parent_id', 'class_teacher', 'class_name', 'active',
            'student_photo', 'certificates', 'certificate_files',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'certificate_files']
        extra_kwargs = {
            'student_photo': {'required': False, 'allow_null': True},
        }

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

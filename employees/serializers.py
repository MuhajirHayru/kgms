from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Employee, Attendance
from accounts.utils import generate_random_password

User = get_user_model()


# ================================
# EMPLOYEE SERIALIZER
# ================================
class EmployeeSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id',
            'phone_number',
            'full_name',
            'role',
            'salary',
        ]


# ================================
# ATTENDANCE SERIALIZER
# ================================
class AttendanceSerializer(serializers.ModelSerializer):
    employee_phone = serializers.CharField(source='employee.user.phone_number', read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id',
            'employee',
            'employee_phone',
            'date',
            'status',
        ]
        read_only_fields = ['date']


# ================================
# EMPLOYEE REGISTRATION SERIALIZER
# ================================
class EmployeeRegistrationSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    phone_number = serializers.CharField()
    role = serializers.ChoiceField(choices=Employee.ROLE_CHOICES)
    salary = serializers.DecimalField(max_digits=10, decimal_places=2)

    def create(self, validated_data):
        phone = validated_data["phone_number"]

        # Ensure unique phone number
        if User.objects.filter(phone_number=phone).exists():
            raise serializers.ValidationError("Phone number already exists")

        # Generate temporary password
        temp_password = generate_random_password()

        # Map Employee role to User role
        role_map = {
            'TEACHER': 'TEACHER',
            'ACCOUNTANT': 'ACCOUNTANT',
            'DRIVER': 'DRIVER',
            'ADMIN': 'DIRECTOR',  # Map Admin to Director in User model
        }
        user_role = role_map.get(validated_data["role"], 'TEACHER')

        # Create User
        user = User.objects.create(
            full_name=validated_data["full_name"],
            phone_number=phone,
            role=user_role,
        )
        user.set_password(temp_password)
        user.save()

        # Create Employee profile
        Employee.objects.create(
            user=user,
            role=validated_data["role"],
            salary=validated_data["salary"],
        )

        # Return credentials for API response
        return {
            "username": phone,
            "temporary_password": temp_password
        }

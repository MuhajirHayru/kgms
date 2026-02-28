from rest_framework import serializers
from .models import User, ParentProfile
from django.db import IntegrityError, transaction

# -------------------------------
# Parent Profile Serializer
# -------------------------------
class ParentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentProfile
        fields = ['id', 'full_name', 'occupation', 'relationship_to_student']


# -------------------------------
# Parent Registration Serializer
# -------------------------------
class ParentRegistrationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    full_name = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True, write_only=True)
    last_name = serializers.CharField(required=False, allow_blank=True, write_only=True)
    occupation = serializers.CharField(required=False, allow_blank=True)
    relationship_to_student = serializers.ChoiceField(
        choices=[('FATHER', 'Father'), ('MOTHER', 'Mother'), ('GUARDIAN', 'Guardian')]
    )

    def validate(self, attrs):
        full_name = (attrs.get("full_name") or "").strip()
        first_name = (attrs.get("first_name") or "").strip()
        last_name = (attrs.get("last_name") or "").strip()

        if not full_name:
            full_name = f"{first_name} {last_name}".strip()

        if not full_name:
            raise serializers.ValidationError(
                {"full_name": ["Provide full_name or first_name/last_name."]}
            )

        attrs["full_name"] = full_name
        return attrs

    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value

    def create(self, validated_data):
        try:
            with transaction.atomic():
                # Create the User
                user = User.objects.create(
                    full_name=validated_data['full_name'],
                    phone_number=validated_data['phone_number'],
                    role='PARENT'
                )
                user.set_password(validated_data['password'])
                user.save()

                # Create ParentProfile
                parent_profile = ParentProfile.objects.create(
                    user=user,
                    full_name=validated_data['full_name'],
                    occupation=validated_data.get('occupation', ''),
                    relationship_to_student=validated_data['relationship_to_student']
                )
                return parent_profile
        except IntegrityError:
            raise serializers.ValidationError(
                {"phone_number": ["A user with this phone number already exists."]}
            )




# -------------------------------
# Parent List Serializer
# -------------------------------
class ParentListSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)

    class Meta:
        model = ParentProfile
        fields = ['id', 'full_name', 'phone_number', 'occupation', 'relationship_to_student']


# -------------------------------
# Admin Reset Password Serializer
# -------------------------------
class AdminResetPasswordSerializer(serializers.Serializer):
    USER_TYPE_CHOICES = (
        ('PARENT', 'Parent'),
        ('EMPLOYEE', 'Employee'),
    )

    phone_number = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    user_type = serializers.ChoiceField(choices=USER_TYPE_CHOICES, required=True)

# -------------------------------
# Change Password Serializer
# -------------------------------
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

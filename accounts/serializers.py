from rest_framework import serializers
from .models import User, ParentProfile

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
    full_name = serializers.CharField(required=True)
    occupation = serializers.CharField(required=False, allow_blank=True)
    relationship_to_student = serializers.ChoiceField(
        choices=[('FATHER', 'Father'), ('MOTHER', 'Mother'), ('GUARDIAN', 'Guardian')]
    )

    def create(self, validated_data):
        # Create the User
        user = User.objects.create(
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


# -------------------------------
# Change Password Serializer
# -------------------------------
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
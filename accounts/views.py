from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ParentProfile, User
from .serializers import (
    AdminResetPasswordSerializer,
    ChangePasswordSerializer,
    ParentListSerializer,
    ParentRegistrationSerializer,
)


class ParentRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ParentRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            parent_profile = serializer.save()
            return Response(
                {
                    "message": "Parent registered successfully",
                    "parent_id": parent_profile.id,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ParentChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data["old_password"]):
                return Response(
                    {"error": "Old password is incorrect"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.set_password(serializer.validated_data["new_password"])
            user.must_change_password = False
            user.save()
            return Response(
                {"message": "Password changed successfully"},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IsDirectorOrSuperuser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.role == "DIRECTOR" or request.user.is_superuser))


class ParentListView(generics.ListAPIView):
    queryset = ParentProfile.objects.select_related("user").all()
    serializer_class = ParentListSerializer
    permission_classes = [IsAuthenticated, IsDirectorOrSuperuser]


class AdminResetUserPasswordView(generics.GenericAPIView):
    serializer_class = AdminResetPasswordSerializer
    permission_classes = [IsAuthenticated, IsDirectorOrSuperuser]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]
        new_password = serializer.validated_data["new_password"]
        user_type = serializer.validated_data["user_type"]

        if user_type == "PARENT":
            user = User.objects.filter(phone_number=phone_number, role="PARENT").first()
        else:
            user = User.objects.exclude(role="PARENT").filter(phone_number=phone_number).first()

        if not user:
            return Response({"error": f"{user_type.title()} not found with this phone number."}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(new_password)
        user.must_change_password = True
        user.save(update_fields=["password", "must_change_password"])

        return Response({"message": f"{user_type.title()} password reset successfully."}, status=status.HTTP_200_OK)

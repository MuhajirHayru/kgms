from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Employee, Attendance
from .serializers import (
    EmployeeSerializer,
    AttendanceSerializer,
    EmployeeRegistrationSerializer
)


# =====================================================
# CUSTOM PERMISSIONS
# =====================================================
class IsDirector(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "DIRECTOR" or request.user.is_superuser

class IsDirectorOrAccountant(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ["DIRECTOR", "ACCOUNTANT"]


class IsOwnerOrStaff(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.user.role in ["DIRECTOR", "ACCOUNTANT"]
            or obj.employee.user == request.user
        )


# =====================================================
# EMPLOYEE REGISTRATION (DIRECTOR ONLY)
# =====================================================

class EmployeeRegisterView(APIView):
    permission_classes = [IsAuthenticated, IsDirector]

    def post(self, request):
        serializer = EmployeeRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.save()
            return Response({
                "message": "Employee registered successfully",
                "credentials": data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================================
# EMPLOYEE LIST (DIRECTOR / ACCOUNTANT)
# =====================================================

class EmployeeListView(generics.ListAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated, IsDirectorOrAccountant]


# =====================================================
# ATTENDANCE VIEWS
# =====================================================

# List attendances
class AttendanceListView(generics.ListAPIView):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role in ["DIRECTOR", "ACCOUNTANT"]:
            return Attendance.objects.all()

        # Employee sees only their own attendance
        return Attendance.objects.filter(employee__user=user)


# Create attendance (Director or Accountant only)
class AttendanceCreateView(generics.CreateAPIView):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, IsDirectorOrAccountant]


# Detail attendance
class AttendanceDetailView(generics.RetrieveAPIView):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]


# Update attendance
class AttendanceUpdateView(generics.UpdateAPIView):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, IsDirectorOrAccountant]

from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({"error": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
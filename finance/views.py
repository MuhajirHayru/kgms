from rest_framework import generics
from .models import Invoice, Payment
from .serializers import InvoiceSerializer, PaymentSerializer

class InvoiceCreateView(generics.CreateAPIView):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer

class PaymentCreateView(generics.CreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

from rest_framework import generics, permissions
from .models import Payroll
from .serializers import PayrollSerializer

# Serializer
from .serializers import PayrollSerializer

# Custom permission
from rest_framework.permissions import BasePermission

class IsDirectorOrAccountant(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['DIRECTOR', 'ACCOUNTANT']

class IsOwnerOrStaff(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.role in ['DIRECTOR', 'ACCOUNTANT'] or obj.employee.user == request.user
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Payroll
from .serializers import PayrollSerializer
from django.utils import timezone

# Custom permissions
class IsDirectorOrAccountant(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['DIRECTOR', 'ACCOUNTANT']

class IsOwnerOrStaff(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.role in ['DIRECTOR', 'ACCOUNTANT'] or obj.employee.user == request.user

# List payrolls
class PayrollListView(generics.ListAPIView):
    serializer_class = PayrollSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ['DIRECTOR', 'ACCOUNTANT']:
            return Payroll.objects.all()
        return Payroll.objects.filter(employee__user=user)

# Detail payroll
class PayrollDetailView(generics.RetrieveAPIView):
    serializer_class = PayrollSerializer
    queryset = Payroll.objects.all()
    permission_classes = [IsOwnerOrStaff]

# Generate payroll for one employee
class PayrollGenerateView(generics.CreateAPIView):
    serializer_class = PayrollSerializer
    permission_classes = [IsDirectorOrAccountant]

# Approve payroll
class PayrollApproveView(generics.UpdateAPIView):
    serializer_class = PayrollSerializer
    queryset = Payroll.objects.all()
    permission_classes = [IsDirectorOrAccountant]

    def patch(self, request, *args, **kwargs):
        payroll = self.get_object()
        payroll.approved = True
        payroll.save()
        return Response(PayrollSerializer(payroll).data)

# Pay payroll
class PayrollPayView(generics.UpdateAPIView):
    serializer_class = PayrollSerializer
    queryset = Payroll.objects.all()
    permission_classes = [IsDirectorOrAccountant]

    def patch(self, request, *args, **kwargs):
        payroll = self.get_object()
        if not payroll.approved:
            return Response({"error": "Payroll must be approved first"}, status=status.HTTP_400_BAD_REQUEST)
        payroll.paid = True
        payroll.paid_at = timezone.now()
        payroll.save()
        return Response(PayrollSerializer(payroll).data)
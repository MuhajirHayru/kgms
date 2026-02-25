from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.utils import timezone

from .models import Invoice, Payment, Payroll
from .serializers import InvoiceSerializer, PaymentSerializer, PayrollSerializer


# ===============================
# 🔐 PERMISSIONS
# ===============================

class IsDirectorOrAccountant(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['DIRECTOR', 'ACCOUNTANT']


class IsOwnerOrStaff(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.user.role in ['DIRECTOR', 'ACCOUNTANT']
            or obj.employee.user == request.user
        )


# ===============================
# 📄 INVOICE VIEWS
# ===============================

class InvoiceCreateView(generics.CreateAPIView):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsDirectorOrAccountant]


class InvoiceListView(generics.ListAPIView):
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        user = self.request.user

        # Parent sees only their children's invoices
        if user.role == "PARENT":
            return Invoice.objects.filter(student__parent=user)

        # Director & Accountant see all
        if user.role in ['DIRECTOR', 'ACCOUNTANT']:
            return Invoice.objects.all()

        return Invoice.objects.none()


# ===============================
# 💳 PAYMENT VIEWS
# ===============================

class PaymentCreateView(generics.CreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role == "PARENT":
            return Payment.objects.filter(invoice__student__parent=user)

        if user.role in ['DIRECTOR', 'ACCOUNTANT']:
            return Payment.objects.all()

        return Payment.objects.none()


# ===============================
# 💰 PAYROLL VIEWS
# ===============================

# List payrolls
class PayrollListView(generics.ListAPIView):
    serializer_class = PayrollSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role in ['DIRECTOR', 'ACCOUNTANT']:
            return Payroll.objects.all()

        # Employee sees only their own payroll
        return Payroll.objects.filter(employee__user=user)


# Detail payroll
class PayrollDetailView(generics.RetrieveAPIView):
    serializer_class = PayrollSerializer
    queryset = Payroll.objects.all()
    permission_classes = [IsOwnerOrStaff]


# Generate payroll
class PayrollGenerateView(generics.CreateAPIView):
    serializer_class = PayrollSerializer
    permission_classes = [IsDirectorOrAccountant]

    def perform_create(self, serializer):
        serializer.save(
            approved=False,
            paid=False
        )


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
            return Response(
                {"error": "Payroll must be approved first"},
                status=status.HTTP_400_BAD_REQUEST
            )

        payroll.paid = True
        payroll.paid_at = timezone.now()
        payroll.save()

        return Response(PayrollSerializer(payroll).data)
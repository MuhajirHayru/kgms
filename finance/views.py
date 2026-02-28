from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.db.models import Sum
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from employees.models import Attendance, Employee

from .models import Bonus, Deduction, Invoice, Payment, Payroll
from .serializers import (
    BonusSerializer,
    DeductionSerializer,
    InvoiceSerializer,
    PaymentSerializer,
    PayrollGenerateSerializer,
    PayrollSerializer,
)


class IsDirectorOrAccountant(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role in ['DIRECTOR', 'ACCOUNTANT'] or request.user.is_superuser
        )


class IsOwnerOrStaff(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.user.role in ['DIRECTOR', 'ACCOUNTANT']
            or request.user.is_superuser
            or obj.employee.user == request.user
        )


class InvoiceCreateView(generics.CreateAPIView):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsDirectorOrAccountant]


class InvoiceListView(generics.ListAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == 'PARENT':
            return Invoice.objects.filter(parent=user)

        if user.role in ['DIRECTOR', 'ACCOUNTANT'] or user.is_superuser:
            return Invoice.objects.all()

        return Invoice.objects.none()


class PaymentCreateView(generics.CreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        payment = serializer.save(paid_by=self.request.user)
        invoice = payment.invoice
        paid_total = invoice.payments.aggregate(total=Sum('paid_amount')).get('total') or Decimal('0')
        if paid_total >= invoice.amount and not invoice.is_paid:
            invoice.is_paid = True
            invoice.save(update_fields=['is_paid'])


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == 'PARENT':
            return Payment.objects.filter(invoice__parent=user)

        if user.role in ['DIRECTOR', 'ACCOUNTANT'] or user.is_superuser:
            return Payment.objects.all()

        return Payment.objects.none()


class PayrollListView(generics.ListAPIView):
    serializer_class = PayrollSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role in ['DIRECTOR', 'ACCOUNTANT'] or user.is_superuser:
            return Payroll.objects.select_related('employee', 'employee__user').all()

        return Payroll.objects.select_related('employee', 'employee__user').filter(employee__user=user)


class PayrollDetailView(generics.RetrieveAPIView):
    serializer_class = PayrollSerializer
    queryset = Payroll.objects.select_related('employee', 'employee__user').all()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]


def _month_bounds(month_str):
    year, month = map(int, month_str.split('-'))
    last_day = monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


class PayrollGenerateView(APIView):
    permission_classes = [IsDirectorOrAccountant]

    def post(self, request):
        serializer = PayrollGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        month = serializer.validated_data['month']
        employee_id = serializer.validated_data.get('employee_id')
        overtime_amount = serializer.validated_data.get('overtime_amount', Decimal('0'))

        try:
            start_date, end_date = _month_bounds(month)
        except Exception:
            return Response(
                {'error': 'Invalid month format. Use YYYY-MM.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        employees = Employee.objects.all()
        if employee_id:
            employees = employees.filter(id=employee_id)

        generated = []
        skipped_paid = []

        for employee in employees:
            present_days = Attendance.objects.filter(
                employee=employee,
                status='PRESENT',
                date__range=[start_date, end_date],
            ).count()

            bonus_total = (
                Bonus.objects.filter(employee=employee, month=month).aggregate(total=Sum('amount')).get('total')
                or Decimal('0')
            )
            deduction_total = (
                Deduction.objects.filter(employee=employee, month=month).aggregate(total=Sum('amount')).get('total')
                or Decimal('0')
            )

            base_salary = employee.salary
            net_salary = base_salary + overtime_amount + bonus_total - deduction_total

            payroll, _ = Payroll.objects.get_or_create(
                employee=employee,
                month=month,
                defaults={
                    'base_salary': base_salary,
                    'total_present_days': present_days,
                    'overtime_amount': overtime_amount,
                    'total_bonus': bonus_total,
                    'total_deductions': deduction_total,
                    'net_salary': net_salary,
                    'status': 'PENDING',
                },
            )

            if payroll.status == 'PAID':
                skipped_paid.append(employee.id)
                continue

            payroll.base_salary = base_salary
            payroll.total_present_days = present_days
            payroll.overtime_amount = overtime_amount
            payroll.total_bonus = bonus_total
            payroll.total_deductions = deduction_total
            payroll.net_salary = net_salary
            if payroll.status not in ['APPROVED', 'PAID']:
                payroll.status = 'PENDING'
            payroll.save()
            generated.append(payroll.id)

        return Response(
            {
                'message': 'Payroll generated successfully.',
                'month': month,
                'generated_payroll_ids': generated,
                'skipped_paid_employee_ids': skipped_paid,
            },
            status=status.HTTP_200_OK,
        )


class PayrollApproveView(APIView):
    permission_classes = [IsDirectorOrAccountant]

    def patch(self, request, pk):
        payroll = Payroll.objects.filter(pk=pk).first()
        if not payroll:
            return Response({'error': 'Payroll not found.'}, status=status.HTTP_404_NOT_FOUND)

        if payroll.status == 'PAID':
            return Response({'error': 'Paid payroll cannot be changed.'}, status=status.HTTP_400_BAD_REQUEST)

        payroll.status = 'APPROVED'
        payroll.save(update_fields=['status'])
        return Response(PayrollSerializer(payroll).data)


class PayrollPayView(APIView):
    permission_classes = [IsDirectorOrAccountant]

    def patch(self, request, pk):
        payroll = Payroll.objects.filter(pk=pk).first()
        if not payroll:
            return Response({'error': 'Payroll not found.'}, status=status.HTTP_404_NOT_FOUND)

        if payroll.status != 'APPROVED':
            return Response(
                {'error': 'Payroll must be approved before payment.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payroll.status = 'PAID'
        payroll.save(update_fields=['status'])
        return Response(PayrollSerializer(payroll).data)


class BonusCreateView(generics.CreateAPIView):
    queryset = Bonus.objects.all()
    serializer_class = BonusSerializer
    permission_classes = [IsDirectorOrAccountant]


class DeductionCreateView(generics.CreateAPIView):
    queryset = Deduction.objects.all()
    serializer_class = DeductionSerializer
    permission_classes = [IsDirectorOrAccountant]

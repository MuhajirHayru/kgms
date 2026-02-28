from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from employees.models import Attendance, Employee

from .models import (
    Bonus,
    CreditRequest,
    DashboardNotification,
    Deduction,
    ExpenseRequest,
    Invoice,
    LedgerEntry,
    Payment,
    Payroll,
    PayrollSetting,
    SchoolAccount,
)
from .serializers import (
    BonusSerializer,
    CreditRepaymentSerializer,
    CreditRequestSerializer,
    CreditReviewSerializer,
    DashboardNotificationSerializer,
    DeductionSerializer,
    EmployeeSalaryUpdateSerializer,
    ExpenseRequestSerializer,
    ExpenseReviewSerializer,
    HideNotificationsSerializer,
    InitializeSchoolAccountSerializer,
    InvoiceSerializer,
    LedgerEntrySerializer,
    ManualIncomeSerializer,
    MonthlyReportSerializer,
    PaymentSerializer,
    PayrollGenerateSerializer,
    PayrollRequestSerializer,
    PayrollReviewSerializer,
    PayrollSerializer,
    PayrollSettingSerializer,
    SchoolAccountSerializer,
)
from .services import record_account_transaction

User = get_user_model()


class IsDirectorOrSuperuser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role == 'DIRECTOR' or request.user.is_superuser
        )


class IsAccountant(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ACCOUNTANT'


class IsDirectorOrAccountant(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role in ['DIRECTOR', 'ACCOUNTANT'] or request.user.is_superuser
        )


class IsEmployeeUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and hasattr(request.user, 'employee_profile'))


class IsOwnerOrStaff(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.user.role in ['DIRECTOR', 'ACCOUNTANT']
            or request.user.is_superuser
            or obj.employee.user == request.user
        )


def _month_bounds(month_str):
    year, month = map(int, month_str.split('-'))
    last_day = monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def _notify_users(users, category, title, message):
    payload = [
        DashboardNotification(
            recipient=user,
            category=category,
            title=title,
            message=message,
        )
        for user in users
    ]
    if payload:
        DashboardNotification.objects.bulk_create(payload)


# -------------------------------
# School Account + Ledger + Reports
# -------------------------------
class SchoolAccountView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorOrAccountant]

    def get(self, request):
        account = SchoolAccount.get_current()
        return Response(SchoolAccountSerializer(account).data)


class SchoolAccountInitializeView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorOrAccountant]

    def post(self, request):
        serializer = InitializeSchoolAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        account = SchoolAccount.get_current()
        if account.is_initialized:
            return Response({'error': 'School account already initialized.'}, status=status.HTTP_400_BAD_REQUEST)

        account.current_balance = serializer.validated_data['initial_balance']
        account.is_initialized = True
        account.save(update_fields=['current_balance', 'is_initialized', 'updated_at'])

        LedgerEntry.objects.create(
            account=account,
            entry_type='OTHER',
            amount_delta=account.current_balance,
            description='Initial school balance set by accountant/admin.',
            created_by=request.user,
        )
        return Response(SchoolAccountSerializer(account).data, status=status.HTTP_201_CREATED)


class ManualIncomeCreateView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorOrAccountant]

    def post(self, request):
        serializer = ManualIncomeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description', '')
        account, _ = record_account_transaction(
            amount_delta=amount,
            entry_type='MANUAL_INCOME',
            description=description or 'Manual income recorded.',
            created_by=request.user,
        )
        return Response(SchoolAccountSerializer(account).data, status=status.HTTP_201_CREATED)


class LedgerEntryListView(generics.ListAPIView):
    serializer_class = LedgerEntrySerializer
    permission_classes = [IsAuthenticated, IsDirectorOrAccountant]

    def get_queryset(self):
        month = self.request.query_params.get('month')  # YYYY-MM
        qs = LedgerEntry.objects.select_related('created_by')
        if month:
            try:
                start, end = _month_bounds(month)
                qs = qs.filter(created_at__date__gte=start, created_at__date__lte=end)
            except Exception:
                pass
        return qs


class MonthlyReportView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorOrAccountant]

    def get(self, request):
        month = request.query_params.get('month')
        if not month:
            month = timezone.localdate().strftime('%Y-%m')

        try:
            start, end = _month_bounds(month)
        except Exception:
            return Response({'error': 'Invalid month format. Use YYYY-MM.'}, status=status.HTTP_400_BAD_REQUEST)

        entries = LedgerEntry.objects.filter(created_at__date__gte=start, created_at__date__lte=end)
        total_income = entries.filter(amount_delta__gt=0).aggregate(total=Sum('amount_delta')).get('total') or Decimal('0')
        total_expense_abs = entries.filter(amount_delta__lt=0).aggregate(total=Sum('amount_delta')).get('total') or Decimal('0')
        total_expense = abs(total_expense_abs)
        profit = total_income - total_expense

        serializer = MonthlyReportSerializer(
            {
                'month': month,
                'total_income': total_income,
                'total_expense': total_expense,
                'profit': profit,
                'entries': entries,
            }
        )
        return Response(serializer.data)


# -------------------------------
# Invoice & Payment (finance app)
# -------------------------------
class InvoiceCreateView(generics.CreateAPIView):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsDirectorOrAccountant]


class InvoiceListView(generics.ListAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        payment = serializer.save(paid_by=self.request.user)
        invoice = payment.invoice
        paid_total = invoice.payments.aggregate(total=Sum('paid_amount')).get('total') or Decimal('0')
        if paid_total >= invoice.amount and not invoice.is_paid:
            invoice.is_paid = True
            invoice.save(update_fields=['is_paid'])

        record_account_transaction(
            amount_delta=payment.paid_amount,
            entry_type='MANUAL_INCOME',
            description=f'Finance payment received for invoice {invoice.id}.',
            created_by=self.request.user,
        )


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == 'PARENT':
            return Payment.objects.filter(invoice__parent=user)

        if user.role in ['DIRECTOR', 'ACCOUNTANT'] or user.is_superuser:
            return Payment.objects.all()

        return Payment.objects.none()


# -------------------------------
# Expense workflow
# -------------------------------
class ExpenseRequestCreateView(generics.CreateAPIView):
    serializer_class = ExpenseRequestSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)
        accountants = User.objects.filter(role='ACCOUNTANT')
        _notify_users(
            accountants,
            'SYSTEM',
            'New Expense Request',
            f'{self.request.user.full_name or self.request.user.phone_number} submitted an expense request.',
        )


class ExpenseRequestListView(generics.ListAPIView):
    serializer_class = ExpenseRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['DIRECTOR', 'ACCOUNTANT'] or user.is_superuser:
            return ExpenseRequest.objects.select_related('requested_by', 'reviewed_by', 'paid_by').all()
        return ExpenseRequest.objects.select_related('requested_by', 'reviewed_by', 'paid_by').filter(requested_by=user)


class ExpenseReviewView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorOrSuperuser]

    def patch(self, request, pk):
        expense = ExpenseRequest.objects.filter(pk=pk).first()
        if not expense:
            return Response({'error': 'Expense request not found.'}, status=status.HTTP_404_NOT_FOUND)

        if expense.status != 'PENDING':
            return Response({'error': 'Only pending requests can be reviewed.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ExpenseReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approve = serializer.validated_data['approve']
        comment = serializer.validated_data.get('comment', '')

        expense.status = 'APPROVED' if approve else 'REJECTED'
        expense.admin_comment = comment
        expense.reviewed_by = request.user
        expense.reviewed_at = timezone.now()
        expense.save(update_fields=['status', 'admin_comment', 'reviewed_by', 'reviewed_at'])

        _notify_users(
            [expense.requested_by],
            'SYSTEM',
            'Expense Review Update',
            f'Your expense request "{expense.title}" was {expense.status.lower()}. Comment: {comment or "No comment"}.',
        )
        return Response(ExpenseRequestSerializer(expense).data)


class ExpenseMarkPaidView(APIView):
    permission_classes = [IsAuthenticated, IsAccountant]

    def patch(self, request, pk):
        expense = ExpenseRequest.objects.filter(pk=pk).first()
        if not expense:
            return Response({'error': 'Expense request not found.'}, status=status.HTTP_404_NOT_FOUND)

        if expense.status != 'APPROVED':
            return Response({'error': 'Only approved expenses can be paid.'}, status=status.HTTP_400_BAD_REQUEST)

        expense.status = 'PAID'
        expense.paid_by = request.user
        expense.paid_at = timezone.now()
        expense.save(update_fields=['status', 'paid_by', 'paid_at'])

        record_account_transaction(
            amount_delta=-expense.amount,
            entry_type='EXPENSE_PAYMENT',
            description=f'Expense paid: {expense.title} ({expense.category}). Reason: {expense.reason}',
            created_by=request.user,
        )

        _notify_users(
            [expense.requested_by],
            'SYSTEM',
            'Expense Paid',
            f'Your expense "{expense.title}" has been paid by accountant.',
        )
        return Response(ExpenseRequestSerializer(expense).data)


# -------------------------------
# Credit workflow
# -------------------------------
class CreditRequestCreateView(generics.CreateAPIView):
    serializer_class = CreditRequestSerializer
    permission_classes = [IsAuthenticated, IsEmployeeUser]

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user.employee_profile)
        accountants = User.objects.filter(role='ACCOUNTANT')
        _notify_users(
            accountants,
            'SYSTEM',
            'New Credit Request',
            f'{self.request.user.full_name or self.request.user.phone_number} requested a credit advance.',
        )


class CreditRequestListView(generics.ListAPIView):
    serializer_class = CreditRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = CreditRequest.objects.select_related('employee', 'employee__user', 'reviewed_by', 'given_by')
        if user.role in ['DIRECTOR', 'ACCOUNTANT'] or user.is_superuser:
            return qs
        if hasattr(user, 'employee_profile'):
            return qs.filter(employee=user.employee_profile)
        return CreditRequest.objects.none()


class CreditReviewView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorOrSuperuser]

    def patch(self, request, pk):
        credit = CreditRequest.objects.filter(pk=pk).select_related('employee', 'employee__user').first()
        if not credit:
            return Response({'error': 'Credit request not found.'}, status=status.HTTP_404_NOT_FOUND)

        if credit.status != 'PENDING':
            return Response({'error': 'Only pending credits can be reviewed.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CreditReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approve = serializer.validated_data['approve']
        comment = serializer.validated_data.get('comment', '')

        credit.status = 'APPROVED' if approve else 'REJECTED'
        credit.admin_comment = comment
        credit.reviewed_by = request.user
        credit.reviewed_at = timezone.now()
        credit.save(update_fields=['status', 'admin_comment', 'reviewed_by', 'reviewed_at'])

        _notify_users(
            [credit.employee.user],
            'SYSTEM',
            'Credit Request Review',
            f'Your credit request was {credit.status.lower()}. Comment: {comment or "No comment"}.',
        )
        accountants = User.objects.filter(role='ACCOUNTANT')
        _notify_users(
            accountants,
            'SYSTEM',
            'Credit Review Result',
            f'Credit request for {credit.employee.user.full_name or credit.employee.user.phone_number} is {credit.status}.',
        )
        return Response(CreditRequestSerializer(credit).data)


class CreditGiveView(APIView):
    permission_classes = [IsAuthenticated, IsAccountant]

    def patch(self, request, pk):
        credit = CreditRequest.objects.filter(pk=pk).select_related('employee', 'employee__user').first()
        if not credit:
            return Response({'error': 'Credit request not found.'}, status=status.HTTP_404_NOT_FOUND)

        if credit.status != 'APPROVED':
            return Response({'error': 'Only approved credits can be given.'}, status=status.HTTP_400_BAD_REQUEST)

        credit.status = 'GIVEN'
        credit.given_by = request.user
        credit.given_at = timezone.now()
        credit.save(update_fields=['status', 'given_by', 'given_at'])

        record_account_transaction(
            amount_delta=-credit.amount,
            entry_type='CREDIT_GIVEN',
            description=(
                f'Credit cash given to {credit.employee.user.full_name or credit.employee.user.phone_number}. '
                f'Reason: {credit.reason}'
            ),
            created_by=request.user,
        )

        _notify_users(
            [credit.employee.user],
            'SYSTEM',
            'Credit Given',
            f'Your approved credit of {credit.amount} has been given by accountant.',
        )
        return Response(CreditRequestSerializer(credit).data)


class CreditRepaymentCreateView(generics.CreateAPIView):
    serializer_class = CreditRepaymentSerializer
    permission_classes = [IsAuthenticated, IsDirectorOrAccountant]

    def perform_create(self, serializer):
        repayment = serializer.save(recorded_by=self.request.user)
        credit = repayment.credit_request

        credit.total_repaid = (credit.total_repaid or Decimal('0')) + repayment.amount
        if credit.total_repaid >= credit.amount:
            credit.status = 'CLOSED'
        credit.save(update_fields=['total_repaid', 'status'])

        record_account_transaction(
            amount_delta=repayment.amount,
            entry_type='CREDIT_REPAYMENT',
            description=(
                f'Credit repayment from {credit.employee.user.full_name or credit.employee.user.phone_number}. '
                f'Credit request #{credit.id}.'
            ),
            created_by=self.request.user,
        )


# -------------------------------
# Payroll process
# -------------------------------
class PayrollListView(generics.ListAPIView):
    serializer_class = PayrollSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == 'ACCOUNTANT':
            return Payroll.objects.select_related('employee', 'employee__user', 'requested_by', 'reviewed_by').all()

        if user.role == 'DIRECTOR' or user.is_superuser:
            return Payroll.objects.select_related('employee', 'employee__user', 'requested_by', 'reviewed_by').filter(
                status__in=['PAYMENT_REQUESTED', 'APPROVED', 'REJECTED', 'PAID']
            )

        return Payroll.objects.select_related('employee', 'employee__user', 'requested_by', 'reviewed_by').filter(
            employee__user=user
        )


class PayrollDetailView(generics.RetrieveAPIView):
    serializer_class = PayrollSerializer
    queryset = Payroll.objects.select_related('employee', 'employee__user', 'requested_by', 'reviewed_by').all()
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]


class PayrollGenerateView(APIView):
    permission_classes = [IsAuthenticated, IsAccountant]

    def post(self, request):
        serializer = PayrollGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        month = serializer.validated_data['month']
        employee_id = serializer.validated_data.get('employee_id')
        overtime_amount = serializer.validated_data.get('overtime_amount', Decimal('0'))

        try:
            start_date, end_date = _month_bounds(month)
        except Exception:
            return Response({'error': 'Invalid month format. Use YYYY-MM.'}, status=status.HTTP_400_BAD_REQUEST)

        employees = Employee.objects.all()
        if employee_id:
            employees = employees.filter(id=employee_id)

        tax_rate = PayrollSetting.get_current().tax_rate_percent

        generated = []
        for employee in employees:
            present_days = Attendance.objects.filter(
                employee=employee,
                status='PRESENT',
                date__range=[start_date, end_date],
            ).count()

            bonus_total = Bonus.objects.filter(employee=employee, month=month).aggregate(total=Sum('amount')).get('total') or Decimal('0')
            deduction_total = Deduction.objects.filter(employee=employee, month=month).aggregate(total=Sum('amount')).get('total') or Decimal('0')

            base_salary = employee.salary
            gross_salary = base_salary + overtime_amount + bonus_total - deduction_total
            tax_amount = (gross_salary * tax_rate) / Decimal('100') if gross_salary > 0 else Decimal('0')
            net_salary = gross_salary - tax_amount

            payroll, _ = Payroll.objects.get_or_create(
                employee=employee,
                month=month,
                defaults={
                    'base_salary': base_salary,
                    'total_present_days': present_days,
                    'overtime_amount': overtime_amount,
                    'total_bonus': bonus_total,
                    'total_deductions': deduction_total,
                    'gross_salary': gross_salary,
                    'tax_rate_percent': tax_rate,
                    'tax_amount': tax_amount,
                    'net_salary': net_salary,
                    'status': 'PENDING',
                },
            )

            if payroll.status == 'PAID':
                continue

            payroll.base_salary = base_salary
            payroll.total_present_days = present_days
            payroll.overtime_amount = overtime_amount
            payroll.total_bonus = bonus_total
            payroll.total_deductions = deduction_total
            payroll.gross_salary = gross_salary
            payroll.tax_rate_percent = tax_rate
            payroll.tax_amount = tax_amount
            payroll.net_salary = net_salary

            if payroll.status in ['REJECTED', 'PENDING']:
                payroll.status = 'PENDING'
                payroll.review_comment = ''
                payroll.reviewed_by = None
                payroll.reviewed_at = None
            payroll.save()
            generated.append(payroll.id)

        return Response(
            {
                'message': 'Payroll generated successfully.',
                'month': month,
                'generated_payroll_ids': generated,
            },
            status=status.HTTP_200_OK,
        )


class PayrollRequestPaymentView(APIView):
    permission_classes = [IsAuthenticated, IsAccountant]

    def post(self, request):
        serializer = PayrollRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payrolls = Payroll.objects.filter(id__in=serializer.validated_data['payroll_ids']).select_related('employee', 'employee__user')
        if not payrolls.exists():
            return Response({'error': 'No payroll records found.'}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()
        for payroll in payrolls:
            if payroll.status in ['PAID', 'APPROVED']:
                continue
            payroll.status = 'PAYMENT_REQUESTED'
            payroll.requested_by = request.user
            payroll.requested_at = now
            payroll.review_comment = ''
            payroll.reviewed_by = None
            payroll.reviewed_at = None
            payroll.save(update_fields=['status', 'requested_by', 'requested_at', 'review_comment', 'reviewed_by', 'reviewed_at'])

        directors = User.objects.filter(role='DIRECTOR') | User.objects.filter(is_superuser=True)
        _notify_users(
            directors.distinct(),
            'PAYROLL_REQUEST',
            'Payroll Payment Request',
            f'Accountant {request.user.full_name or request.user.phone_number} requested payroll approval.',
        )

        return Response({'message': 'Payroll payment request submitted for approval.'}, status=status.HTTP_200_OK)


class PayrollReviewView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorOrSuperuser]

    def patch(self, request, pk):
        payroll = Payroll.objects.filter(pk=pk).select_related('employee', 'employee__user', 'requested_by').first()
        if not payroll:
            return Response({'error': 'Payroll not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PayrollReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if payroll.status != 'PAYMENT_REQUESTED':
            return Response({'error': 'Payroll is not awaiting review.'}, status=status.HTTP_400_BAD_REQUEST)

        approve = serializer.validated_data['approve']
        comment = serializer.validated_data.get('comment', '')

        payroll.status = 'APPROVED' if approve else 'REJECTED'
        payroll.review_comment = comment
        payroll.reviewed_by = request.user
        payroll.reviewed_at = timezone.now()
        payroll.save(update_fields=['status', 'review_comment', 'reviewed_by', 'reviewed_at'])

        if payroll.requested_by:
            _notify_users(
                [payroll.requested_by],
                'PAYROLL_APPROVAL' if approve else 'PAYROLL_REJECTION',
                'Payroll Review Update',
                (
                    f'Payroll for {payroll.employee.user.full_name or payroll.employee.user.phone_number} '
                    f'({payroll.month}) was {"approved" if approve else "rejected"}. '
                    f'Comment: {comment or "No comment"}'
                ),
            )

        return Response(PayrollSerializer(payroll).data, status=status.HTTP_200_OK)


class PayrollPayView(APIView):
    permission_classes = [IsAuthenticated, IsAccountant]

    def patch(self, request, pk):
        payroll = Payroll.objects.filter(pk=pk).select_related('employee', 'employee__user').first()
        if not payroll:
            return Response({'error': 'Payroll not found.'}, status=status.HTTP_404_NOT_FOUND)

        if payroll.status != 'APPROVED':
            return Response({'error': 'Payroll must be approved before payment.'}, status=status.HTTP_400_BAD_REQUEST)

        payroll.status = 'PAID'
        payroll.save(update_fields=['status'])

        record_account_transaction(
            amount_delta=-payroll.net_salary,
            entry_type='SALARY_PAYMENT',
            description=f'Salary paid for {payroll.employee.user.full_name or payroll.employee.user.phone_number} ({payroll.month}).',
            created_by=request.user,
        )

        _notify_users(
            [payroll.employee.user],
            'PAYROLL_PAID',
            'Monthly Salary Paid',
            f'Your salary for {payroll.month} has been paid. Net amount: {payroll.net_salary}.',
        )

        directors = User.objects.filter(role='DIRECTOR') | User.objects.filter(is_superuser=True)
        _notify_users(
            directors.distinct(),
            'PAYROLL_PAID',
            'Employee Paid',
            f'Paid: {payroll.employee.user.full_name or payroll.employee.user.phone_number} for {payroll.month}.',
        )

        return Response(PayrollSerializer(payroll).data, status=status.HTTP_200_OK)


# -------------------------------
# Bonus/Deduction and settings
# -------------------------------
class BonusCreateView(generics.CreateAPIView):
    queryset = Bonus.objects.all()
    serializer_class = BonusSerializer
    permission_classes = [IsDirectorOrAccountant]


class DeductionCreateView(generics.CreateAPIView):
    queryset = Deduction.objects.all()
    serializer_class = DeductionSerializer
    permission_classes = [IsDirectorOrAccountant]


class PayrollSettingView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorOrSuperuser]

    def get(self, request):
        setting = PayrollSetting.get_current()
        return Response(PayrollSettingSerializer(setting).data)

    def put(self, request):
        setting = PayrollSetting.get_current()
        serializer = PayrollSettingSerializer(setting, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class EmployeeSalaryUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorOrSuperuser]

    def patch(self, request):
        serializer = EmployeeSalaryUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        employee = Employee.objects.filter(id=serializer.validated_data['employee_id']).first()
        if not employee:
            return Response({'error': 'Employee not found.'}, status=status.HTTP_404_NOT_FOUND)

        employee.salary = serializer.validated_data['salary']
        employee.save(update_fields=['salary'])

        return Response(
            {
                'message': 'Employee salary updated successfully.',
                'employee_id': employee.id,
                'new_salary': str(employee.salary),
            },
            status=status.HTTP_200_OK,
        )


# -------------------------------
# Dashboard notifications
# -------------------------------
class DashboardNotificationListView(generics.ListAPIView):
    serializer_class = DashboardNotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DashboardNotification.objects.filter(recipient=self.request.user, is_hidden=False)


class HideDashboardNotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = HideNotificationsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        hide_all = serializer.validated_data['hide_all']
        ids = serializer.validated_data['notification_ids']

        qs = DashboardNotification.objects.filter(recipient=request.user, is_hidden=False)
        if hide_all:
            updated = qs.update(is_hidden=True)
            return Response({'message': 'All notifications removed from dashboard.', 'updated': updated})

        if not ids:
            return Response({'error': 'Provide notification_ids or set hide_all=true.'}, status=status.HTTP_400_BAD_REQUEST)

        updated = qs.filter(id__in=ids).update(is_hidden=True)
        return Response({'message': 'Selected notifications removed from dashboard.', 'updated': updated})

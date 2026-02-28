from decimal import Decimal
from datetime import timedelta
from django.db.models import Sum
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Invoice, Parent, ParentNotification, Payment, PenaltySetting, Student
from .serializers import (
    AccountantDashboardSerializer,
    InvoiceSerializer,
    ParentNotificationSerializer,
    ParentSerializer,
    PaymentSerializer,
    PenaltySettingSerializer,
    StudentSerializer,
)
from finance.services import record_account_transaction


class IsDirectorOrAccountant(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in ["DIRECTOR", "ACCOUNTANT"]
        ) or request.user.is_superuser


class IsDirectorOrSuperuser(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "DIRECTOR"
        ) or request.user.is_superuser


def _month_key(date_obj):
    return date_obj.strftime("%Y-%m")


def _apply_penalty(invoice):
    if invoice.is_paid:
        return invoice

    setting = PenaltySetting.get_current()
    today = timezone.localdate()
    if invoice.due_date >= today:
        return invoice

    overdue_days = (today - invoice.due_date).days
    new_penalty = Decimal(overdue_days) * setting.penalty_per_day
    if invoice.penalty_amount != new_penalty:
        invoice.penalty_amount = new_penalty
        invoice.save(update_fields=["penalty_amount"])
    return invoice

# ---- Parent Views ----
class ParentListCreateView(generics.ListCreateAPIView):
    queryset = Parent.objects.filter(role='PARENT')
    serializer_class = ParentSerializer
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]


class ParentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Parent.objects.filter(role='PARENT')
    serializer_class = ParentSerializer
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]


# ---- Student Views ----
class StudentListCreateView(generics.ListCreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]


class StudentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]


# ---- Invoice Views ----
class InvoiceListCreateView(generics.ListCreateAPIView):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset().select_related("student")
        for invoice in queryset:
            _apply_penalty(invoice)
        return queryset


# ---- Payment Views ----
class PaymentListCreateView(generics.ListCreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        payment = serializer.save(paid_by=self.request.user)
        invoice = payment.invoice
        _apply_penalty(invoice)
        record_account_transaction(
            amount_delta=payment.amount,
            entry_type="STUDENT_FEE",
            description=(
                f"Student fee received from {invoice.student.parent.full_name or invoice.student.parent.phone_number} "
                f"for {invoice.student} ({invoice.month})."
            ),
            created_by=self.request.user,
        )

        total_paid = invoice.payments.aggregate(total=Sum("amount")).get("total") or Decimal("0")
        total_due = invoice.total_amount_due
        if total_paid >= total_due and not invoice.is_paid:
            invoice.is_paid = True
            invoice.save(update_fields=["is_paid"])
            ParentNotification.objects.create(
                parent=invoice.student.parent,
                student=invoice.student,
                invoice=invoice,
                notification_type="THANK_YOU",
                title="Payment Received",
                message=(
                    f"Thank you. Payment for {invoice.student} ({invoice.month}) "
                    "has been received successfully."
                ),
            )


class PenaltySettingView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorOrSuperuser]

    def get(self, request):
        setting = PenaltySetting.get_current()
        return Response(PenaltySettingSerializer(setting).data)

    def put(self, request):
        setting = PenaltySetting.get_current()
        serializer = PenaltySettingSerializer(setting, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class GenerateCurrentMonthInvoicesView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorOrAccountant]

    def post(self, request):
        today = timezone.localdate()
        month = _month_key(today)
        due_day = int(request.data.get("due_day", 5))
        due_day = max(1, min(due_day, 28))
        due_date = today.replace(day=due_day)

        created = 0
        active_students = Student.objects.filter(active=True).select_related("parent")
        for student in active_students:
            _, was_created = Invoice.objects.get_or_create(
                student=student,
                month=month,
                defaults={
                    "amount": student.monthly_tuition_fee,
                    "due_date": due_date,
                },
            )
            if was_created:
                created += 1

        return Response(
            {"message": "Current month invoices generated.", "month": month, "created": created},
            status=status.HTTP_201_CREATED,
        )


class AccountantMonthlyDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorOrAccountant]

    def get(self, request):
        month = request.query_params.get("month") or _month_key(timezone.localdate())
        invoices = Invoice.objects.filter(month=month).select_related("student", "student__parent")
        for invoice in invoices:
            _apply_penalty(invoice)

        paid_qs = invoices.filter(is_paid=True)
        unpaid_qs = invoices.filter(is_paid=False)
        overdue_qs = unpaid_qs.filter(due_date__lt=timezone.localdate())

        payload = {
            "month": month,
            "total_students": invoices.count(),
            "paid_students": paid_qs.count(),
            "unpaid_students": unpaid_qs.count(),
            "overdue_students": overdue_qs.count(),
            "paid_invoices": paid_qs,
            "unpaid_invoices": unpaid_qs,
        }
        serializer = AccountantDashboardSerializer(payload)
        return Response(serializer.data)


class ReminderRunView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorOrAccountant]

    def post(self, request):
        today = timezone.localdate()
        target_due_date = today + timedelta(days=3)
        invoices = Invoice.objects.filter(is_paid=False, due_date=target_due_date).select_related(
            "student", "student__parent"
        )

        created = 0
        for invoice in invoices:
            exists = ParentNotification.objects.filter(
                parent=invoice.student.parent,
                invoice=invoice,
                notification_type="REMINDER",
            ).exists()
            if exists:
                continue
            ParentNotification.objects.create(
                parent=invoice.student.parent,
                student=invoice.student,
                invoice=invoice,
                notification_type="REMINDER",
                title="Tuition Reminder",
                message=(
                    f"Reminder: Tuition for {invoice.student} ({invoice.month}) is due on "
                    f"{invoice.due_date}."
                ),
            )
            created += 1

        return Response({"message": "Reminder run completed.", "reminders_created": created})


class ParentNotificationListView(generics.ListAPIView):
    serializer_class = ParentNotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role != "PARENT":
            return ParentNotification.objects.none()
        return ParentNotification.objects.filter(parent=user).select_related("student", "invoice")

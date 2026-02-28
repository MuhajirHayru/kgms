from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone

from students.models import Invoice, ParentNotification, PenaltySetting, Student


def month_key(date_obj):
    return date_obj.strftime("%Y-%m")


class Command(BaseCommand):
    help = (
        "Generates current-month invoices for active students, applies overdue penalties, "
        "and sends reminders 3 days before due date."
    )

    def add_arguments(self, parser):
        parser.add_argument("--due-day", type=int, default=5)

    def handle(self, *args, **options):
        today = timezone.localdate()
        due_day = max(1, min(int(options["due_day"]), 28))
        due_date = today.replace(day=due_day)
        current_month = month_key(today)

        created_invoices = 0
        for student in Student.objects.filter(active=True):
            _, created = Invoice.objects.get_or_create(
                student=student,
                month=current_month,
                defaults={
                    "amount": student.monthly_tuition_fee,
                    "due_date": due_date,
                },
            )
            if created:
                created_invoices += 1

        penalty_setting = PenaltySetting.get_current()
        updated_penalties = 0
        unpaid_invoices = Invoice.objects.filter(is_paid=False)
        for invoice in unpaid_invoices:
            if invoice.due_date >= today:
                continue
            overdue_days = (today - invoice.due_date).days
            expected_penalty = Decimal(overdue_days) * penalty_setting.penalty_per_day
            if invoice.penalty_amount != expected_penalty:
                invoice.penalty_amount = expected_penalty
                invoice.save(update_fields=["penalty_amount"])
                updated_penalties += 1

            total_paid = invoice.payments.aggregate(total=Sum("amount")).get("total") or Decimal("0")
            if total_paid >= invoice.total_amount_due:
                invoice.is_paid = True
                invoice.save(update_fields=["is_paid"])

        reminders_created = 0
        target_due = today + timedelta(days=3)
        due_soon_invoices = Invoice.objects.filter(is_paid=False, due_date=target_due).select_related(
            "student", "student__parent"
        )
        for invoice in due_soon_invoices:
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
            reminders_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Created invoices: {created_invoices}, "
                f"updated penalties: {updated_penalties}, reminders: {reminders_created}"
            )
        )

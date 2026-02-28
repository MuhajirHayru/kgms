from django.conf import settings
from django.db import models
from students.models import Parent
from accounts.models import User

class Invoice(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='invoices')
    month = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    due_date = models.DateField()
class Payment(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_at = models.DateTimeField(auto_now_add=True)
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # or User
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='finance_payments'  # <-- unique related_name
    )
from django.db import models
from employees.models import Employee


class Payroll(models.Model):

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PAYMENT_REQUESTED', 'Payment Requested'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PAID', 'Paid'),
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="payrolls"
    )

    month = models.CharField(max_length=20)
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)

    total_present_days = models.IntegerField(default=0)
    overtime_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    total_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_rate_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    net_salary = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_payrolls",
    )
    requested_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_payrolls",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comment = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee} - {self.month}"

class Bonus(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()

class Deduction(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()


class PayrollSetting(models.Model):
    # Single active row by convention (id=1)
    tax_rate_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Tax rate: {self.tax_rate_percent}%"

    @classmethod
    def get_current(cls):
        obj, _ = cls.objects.get_or_create(id=1, defaults={"tax_rate_percent": 0})
        return obj


class DashboardNotification(models.Model):
    CATEGORY_CHOICES = (
        ("PAYROLL_REQUEST", "Payroll Request"),
        ("PAYROLL_APPROVAL", "Payroll Approval"),
        ("PAYROLL_REJECTION", "Payroll Rejection"),
        ("PAYROLL_PAID", "Payroll Paid"),
        ("SYSTEM", "System"),
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dashboard_notifications",
    )
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default="SYSTEM")
    title = models.CharField(max_length=150)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient} - {self.category} - {self.title}"


class SchoolAccount(models.Model):
    current_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_initialized = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_current(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj

    def __str__(self):
        return f"School Balance: {self.current_balance}"


class LedgerEntry(models.Model):
    ENTRY_TYPE_CHOICES = (
        ("STUDENT_FEE", "Student Fee"),
        ("MANUAL_INCOME", "Manual Income"),
        ("SALARY_PAYMENT", "Salary Payment"),
        ("EXPENSE_PAYMENT", "Expense Payment"),
        ("CREDIT_GIVEN", "Credit Given"),
        ("CREDIT_REPAYMENT", "Credit Repayment"),
        ("OTHER", "Other"),
    )

    account = models.ForeignKey(SchoolAccount, on_delete=models.CASCADE, related_name="entries")
    entry_type = models.CharField(max_length=30, choices=ENTRY_TYPE_CHOICES, default="OTHER")
    amount_delta = models.DecimalField(max_digits=14, decimal_places=2)
    description = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_ledger_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.entry_type}: {self.amount_delta}"


class ExpenseRequest(models.Model):
    CATEGORY_CHOICES = (
        ("FUEL", "Fuel"),
        ("GARAGE", "Garage"),
        ("OTHER", "Other"),
    )
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("PAID", "Paid"),
    )

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="expense_requests"
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="OTHER")
    title = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    admin_comment = models.TextField(blank=True, default="")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_expense_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="paid_expense_requests",
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.amount} ({self.status})"


class CreditRequest(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("GIVEN", "Given"),
        ("CLOSED", "Closed"),
    )

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="credit_requests")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    admin_comment = models.TextField(blank=True, default="")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_credit_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    given_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="given_credit_requests",
    )
    given_at = models.DateTimeField(null=True, blank=True)
    total_repaid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Credit {self.employee} - {self.amount} ({self.status})"


class CreditRepayment(models.Model):
    credit_request = models.ForeignKey(
        CreditRequest, on_delete=models.CASCADE, related_name="repayments"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_credit_repayments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Repayment {self.amount} - Credit #{self.credit_request_id}"

# students/models.py
from django.db import models
from django.conf import settings
from employees.models import Employee
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

# Choices
GENDER_CHOICES = (
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
)

STUDENT_CATEGORY_CHOICES = (
    ('KG', 'KG'),
    ('ELEMENTARY', 'Elementary'),
)

GRADE_LEVEL_CHOICES = (
    ('KG1', 'KG 1'),
    ('KG2', 'KG 2'),
    ('KG3', 'KG 3'),
    ('GRADE1', 'Grade 1'),
    ('GRADE2', 'Grade 2'),
    ('GRADE3', 'Grade 3'),
    ('GRADE4', 'Grade 4'),
    ('GRADE5', 'Grade 5'),
    ('GRADE6', 'Grade 6'),
    ('GRADE7', 'Grade 7'),
    ('GRADE8', 'Grade 8'),
)

TRANSPORT_CHOICES = (
    ('BUS', 'Bus'),
    ('FOOT', 'Foot'),
)

class Student(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    dob = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    category = models.CharField(max_length=20, choices=STUDENT_CATEGORY_CHOICES, default='KG')
    grade_level = models.CharField(max_length=20, choices=GRADE_LEVEL_CHOICES, default='KG1')
    transport = models.CharField(max_length=10, choices=TRANSPORT_CHOICES, default='FOOT')
    address = models.TextField(blank=True, null=True)
    emergency_contact = models.CharField(max_length=50, blank=True, null=True)

    # Parent must be USER with role = PARENT
    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="children",
        limit_choices_to={'role': 'PARENT'}
    )

    # Assign class teacher
    class_teacher = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'TEACHER'},
        related_name="students"
    )

    class_name = models.CharField(max_length=50)
    monthly_tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    active = models.BooleanField(default=True)
    student_photo = models.FileField(upload_to="students/photos/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class StudentCertificate(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="certificates",
    )
    file = models.FileField(upload_to="students/certificates/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Certificate - {self.student}"


class Invoice(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="invoices"
    )
    month = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    penalty_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Invoice - {self.student} - {self.month}"

    @property
    def total_amount_due(self):
        return self.amount + self.penalty_amount


class Payment(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(auto_now_add=True)
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_payments"  # Unique related_name to avoid clashes
    )

    def __str__(self):
        return f"Payment {self.amount} - {self.invoice}"


class PenaltySetting(models.Model):
    # Keep a single active settings row by convention.
    penalty_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Penalty/day: {self.penalty_per_day}"

    @classmethod
    def get_current(cls):
        obj, _ = cls.objects.get_or_create(id=1, defaults={"penalty_per_day": 0})
        return obj


class StudentFeeSetting(models.Model):
    kg_monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    elementary_monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bus_transport_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Student Fee Settings"

    @classmethod
    def get_current(cls):
        obj, _ = cls.objects.get_or_create(
            id=1,
            defaults={
                "kg_monthly_fee": 0,
                "elementary_monthly_fee": 0,
                "registration_fee": 0,
                "bus_transport_fee": 0,
            },
        )
        return obj


class ParentNotification(models.Model):
    NOTIFICATION_TYPES = (
        ("REMINDER", "Reminder"),
        ("THANK_YOU", "Thank You"),
    )

    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="parent_notifications",
        limit_choices_to={"role": "PARENT"},
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="notifications")
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=120)
    message = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-sent_at"]

    def __str__(self):
        return f"{self.notification_type} - {self.parent} - {self.student}"


class Parent(User):
    class Meta:
        proxy = True  # Not a new table
        verbose_name = "Parent"
        verbose_name_plural = "Parents"

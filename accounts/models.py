from django.contrib.auth.models import AbstractUser
from django.db import models

# -------------------------------
# Core User Model
# -------------------------------
class User(AbstractUser):
    ROLE_CHOICES = (
        ('DIRECTOR', 'Director'),
        ('ACCOUNTANT', 'Accountant'),
        ('DRIVER', 'Driver'),
        ('TEACHER', 'Teacher'),
        ('PARENT', 'Parent'),
    )

    username = None  # remove default username field
    first_name = None
    last_name = None
    email = None
    full_name = models.CharField(max_length=150, blank=True, default="")
    phone_number = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    must_change_password = models.BooleanField(default=True)

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    def __str__(self):
        label = self.full_name or self.phone_number
        return f"{label} ({self.role})"


# -------------------------------
# Parent Profile (Extra info for parents only)
# -------------------------------
class ParentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')
    full_name = models.CharField(max_length=100)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    relationship_to_student = models.CharField(
        max_length=20,
        choices=(('FATHER', 'Father'), ('MOTHER', 'Mother'), ('GUARDIAN', 'Guardian'))
    )

    def __str__(self):
        return f"{self.full_name} ({self.relationship_to_student})"


# -------------------------------
# Driver Profile (Example for other roles)
# -------------------------------
class DriverProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile')
    license_number = models.CharField(max_length=50)

    def __str__(self):
        return self.user.phone_number

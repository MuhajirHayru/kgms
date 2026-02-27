from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

# -------------------------------
# Core User Model
# -------------------------------
class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, phone_number, password, **extra_fields):
        if not phone_number:
            raise ValueError("The phone number must be set")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", "PARENT")
        return self._create_user(phone_number, password, **extra_fields)

    def create_superuser(self, phone_number, password=None, **extra_fields):
        username = extra_fields.get("username")
        if not username:
            raise ValueError("Superuser must have a username.")

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "DIRECTOR")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(phone_number, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = (
        ('DIRECTOR', 'Director'),
        ('ACCOUNTANT', 'Accountant'),
        ('DRIVER', 'Driver'),
        ('TEACHER', 'Teacher'),
        ('PARENT', 'Parent'),
    )

    username = models.CharField(max_length=150, unique=True, null=True, blank=True, default=None)
    first_name = None
    last_name = None
    email = None
    full_name = models.CharField(max_length=150, blank=True, default="")
    phone_number = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    must_change_password = models.BooleanField(default=True)

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["username"]
    objects = UserManager()

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

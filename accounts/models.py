from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('DIRECTOR', 'Director'),
        ('ACCOUNTANT', 'Accountant'),
        ('DRIVER', 'Driver'),
        ('TEACHER', 'Teacher'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='TEACHER')

class DriverProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile')
    license_number = models.CharField(max_length=50)

    def __str__(self):
        return self.user.username
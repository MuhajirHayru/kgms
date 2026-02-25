from django.db import models
from accounts.models import DriverProfile

class Route(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Bus(models.Model):
    bus_number = models.CharField(max_length=20, unique=True)
    plate_number = models.CharField(max_length=20)
    capacity = models.PositiveIntegerField()
    driver = models.ForeignKey(DriverProfile, on_delete=models.SET_NULL, null=True, blank=True)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='buses')

    def __str__(self):
        return f"{self.bus_number} ({self.plate_number})"

class BusAssignment(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='bus_assignments')
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='student_assignments')
    assigned_date = models.DateField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['student','bus'], name='unique_student_bus')]

class DriverAlert(models.Model):
    ALERT_TYPES = (('ARRIVAL','Arrival'),('DELAY','Delay'),('ACCIDENT','Accident'))
    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE, related_name='alerts')
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class FuelRequest(models.Model):
    STATUS_CHOICES = (('PENDING','Pending'),('APPROVED','Approved'),('REJECTED','Rejected'))
    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE, related_name='fuel_requests')
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='fuel_requests')
    requested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    purpose = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_fuel_requests')
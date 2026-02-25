from django.db import models
from django.conf import settings
from students.models import Student


class ChatRoom(models.Model):

    ROOM_TYPES = (
        ('PARENT_TEACHER', 'Parent-Teacher'),
        ('PARENT_ACCOUNTANT', 'Parent-Accountant'),
        ('DRIVER_ACCOUNTANT', 'Driver-Accountant'),
    )

    room_type = models.CharField(max_length=30, choices=ROOM_TYPES)

    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="parent_rooms"
    )

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="teacher_rooms"
    )

    accountant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="accountant_rooms"
    )

    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="driver_rooms"
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.room_type} Room"
    
class Message(models.Model):

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    content = models.TextField(blank=True, null=True)

    file = models.FileField(upload_to="chat_files/", null=True, blank=True)
    image = models.ImageField(upload_to="chat_images/", null=True, blank=True)

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
class UserOnlineStatus(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.is_online}"
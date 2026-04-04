from django.db import models
from django.conf import settings
from students.models import Student


class ChatRoom(models.Model):

    ROOM_TYPES = (
        ('PARENT_TEACHER', 'Parent-Teacher'),
        ('PARENT_ACCOUNTANT', 'Parent-Accountant'),
        ('PARENT_ADMIN', 'Parent-Admin'),
        ('DRIVER_ACCOUNTANT', 'Driver-Accountant'),
        ('DRIVER_ADMIN', 'Driver-Admin'),
        ('DRIVER_PARENT', 'Driver-Parent'),
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

    director = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="director_rooms"
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

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.room_type} Room"


class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_messages")

    content = models.TextField(blank=True, null=True)

    file = models.FileField(upload_to="chat_files/", null=True, blank=True)
    image = models.ImageField(upload_to="chat_images/", null=True, blank=True)

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        sender_label = self.sender.full_name or self.sender.phone_number
        return f"{sender_label}: {self.content or 'Attachment'}"


class UserOnlineStatus(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        user_label = self.user.full_name or self.user.phone_number or self.user.username
        return f"{user_label} - {self.is_online}"

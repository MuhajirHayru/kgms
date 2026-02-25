from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Student
from chat.services import create_parent_teacher_room


@receiver(post_save, sender=Student)
def auto_create_chat(sender, instance, created, **kwargs):
    if created and instance.class_teacher:
        create_parent_teacher_room(instance)
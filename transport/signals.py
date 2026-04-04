from django.db.models.signals import post_save
from django.dispatch import receiver

from chat.services import ensure_driver_parent_room
from .models import BusAssignment


@receiver(post_save, sender=BusAssignment)
def create_driver_parent_chat_room(sender, instance, created, **kwargs):
    if not created:
        return
    driver_profile = instance.bus.driver
    if driver_profile and driver_profile.user_id:
        ensure_driver_parent_room(instance.student, driver_profile.user)

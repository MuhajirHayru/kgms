from django.contrib import admin

from .models import ChatRoom, Message, UserOnlineStatus


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "room_type", "parent", "teacher", "accountant", "director", "driver", "student", "created_at")
    list_filter = ("room_type",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "sender", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("content",)


@admin.register(UserOnlineStatus)
class UserOnlineStatusAdmin(admin.ModelAdmin):
    list_display = ("user", "is_online", "last_seen")
    list_filter = ("is_online",)

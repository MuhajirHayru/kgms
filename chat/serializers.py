from rest_framework import serializers

from .models import ChatRoom, Message, UserOnlineStatus


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.full_name", read_only=True)
    sender_role = serializers.CharField(source="sender.role", read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "room",
            "sender",
            "sender_name",
            "sender_role",
            "content",
            "file",
            "image",
            "is_read",
            "created_at",
        ]
        read_only_fields = ["id", "room", "sender", "sender_name", "sender_role", "is_read", "created_at"]

    def validate(self, attrs):
        if not attrs.get("content") and not attrs.get("file") and not attrs.get("image"):
            raise serializers.ValidationError("Message must include text, file, or image.")
        return attrs


class ChatRoomSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    counterpart_name = serializers.SerializerMethodField()
    counterpart_role = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            "id",
            "room_type",
            "parent",
            "teacher",
            "accountant",
            "director",
            "driver",
            "student",
            "created_at",
            "last_message",
            "unread_count",
            "counterpart_name",
            "counterpart_role",
        ]
        read_only_fields = fields

    def get_last_message(self, obj):
        last_message = obj.messages.select_related("sender").order_by("-created_at", "-id").first()
        if not last_message:
            return None
        return MessageSerializer(last_message, context=self.context).data

    def get_unread_count(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return 0
        return obj.messages.filter(is_read=False).exclude(sender=user).count()

    def get_counterpart_name(self, obj):
        counterpart = self._get_counterpart(obj)
        if counterpart is None:
            return None
        return counterpart.full_name or counterpart.phone_number

    def get_counterpart_role(self, obj):
        counterpart = self._get_counterpart(obj)
        if counterpart is None:
            return None
        return counterpart.role

    def _get_counterpart(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None

        candidates = [obj.parent, obj.teacher, obj.accountant, obj.director, obj.driver]
        for candidate in candidates:
            if candidate and candidate != user:
                return candidate
        return None


class UserOnlineStatusSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = UserOnlineStatus
        fields = ["user", "user_name", "is_online", "last_seen"]
        read_only_fields = fields

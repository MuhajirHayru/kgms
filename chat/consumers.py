import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import ChatRoom, Message, UserOnlineStatus
from .permissions import can_access_room


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"
        self.room = await self._get_room(self.room_id)
        if self.room is None:
            await self.close(code=4004)
            return

        has_access = await self._user_can_access_room(user, self.room)
        if not has_access:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self._set_online_status(user, True)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        user = self.scope.get("user")
        if user and user.is_authenticated:
            await self._set_online_status(user, False)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            await self.send(text_data=json.dumps({"error": "Only JSON text messages are supported."}))
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"error": "Invalid JSON payload."}))
            return

        content = (data.get("message") or data.get("content") or "").strip()
        if not content:
            await self.send(text_data=json.dumps({"error": "Message content is required."}))
            return

        message = await self._create_message(
            room_id=self.room_id,
            sender_id=self.scope["user"].id,
            content=content,
        )
        payload = {
            "type": "chat.message",
            "message": {
                "id": message["id"],
                "room_id": message["room_id"],
                "content": message["content"],
                "sender_id": message["sender_id"],
                "sender_name": message["sender_name"],
                "sender_role": message["sender_role"],
                "created_at": message["created_at"],
                "is_read": False,
            },
        }
        await self.channel_layer.group_send(self.room_group_name, payload)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    @database_sync_to_async
    def _get_room(self, room_id):
        return ChatRoom.objects.select_related("parent", "teacher", "accountant", "director", "driver").filter(pk=room_id).first()

    @database_sync_to_async
    def _user_can_access_room(self, user, room):
        return can_access_room(user, room)

    @database_sync_to_async
    def _create_message(self, room_id, sender_id, content):
        message = Message.objects.create(
            room_id=room_id,
            sender_id=sender_id,
            content=content,
        )
        sender = message.sender
        return {
            "id": message.id,
            "room_id": message.room_id,
            "content": message.content,
            "sender_id": sender.id,
            "sender_name": sender.full_name or sender.phone_number,
            "sender_role": sender.role,
            "created_at": message.created_at.isoformat(),
        }

    @database_sync_to_async
    def _set_online_status(self, user, is_online):
        UserOnlineStatus.objects.update_or_create(
            user=user,
            defaults={"is_online": is_online},
        )

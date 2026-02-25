import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChatRoom, Message


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):

        data = json.loads(text_data)
        message = data['message']

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    async def chat_message(self, event):

        message = event['message']

        await self.send(text_data=json.dumps({
            'message': message
        }))
 # this is online user tracking 
from .models import UserOnlineStatus

async def connect(self):
    user = self.scope["user"]
    UserOnlineStatus.objects.update_or_create(
        user=user,
        defaults={"is_online": True}
    )

    await self.channel_layer.group_send(
    "online_users",
    {
        "type": "user_online",
        "user_id": self.scope["user"].id
    }
)

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.room_name = f"chat_{self.user.id}"
        self.room_group_name = f"chat_{self.user.id}"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender_id = self.user.id
        receiver_id = data['receiver_id']

        # Lưu tin nhắn vào DB (tuỳ chọn)
        await self.save_message(sender_id, receiver_id, message)

        # Gửi tin nhắn đến người nhận
        await self.channel_layer.group_send(
            f"chat_{receiver_id}",
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': sender_id,
            }
        )

    async def chat_message(self, event):
        # Gửi tin nhắn qua WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
        }))

    @staticmethod
    async def save_message(sender_id, receiver_id, message):
        from .models import Message
        from django.contrib.auth.models import User
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)
        Message.objects.create(sender=sender, receiver=receiver, content=message)

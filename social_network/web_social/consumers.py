# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.receiver_id = self.scope["url_route"]["kwargs"]["receiver_id"]
        self.room_name = f"chat_{min(self.user.id, self.receiver_id)}_{max(self.user.id, self.receiver_id)}"
        self.accept()
        # Tham gia vào nhóm chat
        # await self.channel_layer.group_add(
        #     self.room_name,
        #     self.channel_name
        # )
        # await self.accept()

    async def disconnect(self, close_code):
        # Rời khỏi nhóm chat
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )


    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]



        # Gửi tin nhắn đến nhóm chat
        await self.channel_layer.group_send(
            self.room_name,
            {
                "type": "chat_message",
                "message": message,
                "sender": self.user.username
            }

        )



    async def chat_message(self, event):
        message = event["message"]
        sender = event["sender"]

        # Gửi tin nhắn đến WebSocket
        await self.send(text_data=json.dumps({
            "message": message,
            "sender": sender
        }))

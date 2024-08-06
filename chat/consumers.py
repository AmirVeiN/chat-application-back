import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Room, Message
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class ContactsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_anonymous:
            await self.close()
        else:
            self.group_name = f"contacts_group_{self.user.username}"
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def update_contacts(self, event):
        contacts = event['contacts']
        await self.send(text_data=json.dumps({
            'type': 'update_contacts',
            'contacts': contacts
        }))

    @sync_to_async
    def get_contacts(self, user):
        rooms = Room.objects.filter(participants=user).distinct()
        contacts = set()
        for room in rooms:
            for participant in room.participants.all():
                if participant != user:
                    contacts.add(participant)
        return [{"id": contact.id, "username": contact.username} for contact in contacts]

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        messages = await self.get_initial_messages(self.room_name)
        await self.send(text_data=json.dumps({
            "type": "initial_messages",
            "messages": messages
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data["message"]
        username = data["username"]

        room = await self.get_room(self.room_name)
        user = await self.get_user(username)

        msg = await self.create_message(room, user, message_content)

        await self.update_contacts(room)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": {
                    "user": user.username,
                    "content": msg.content,
                    'timestamp': msg.timestamp.isoformat()
                },
            },
        )

    async def chat_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": message
        }))

    @sync_to_async
    def get_room(self, room_name):
        return Room.objects.get(name=room_name)

    @sync_to_async
    def get_user(self, username):
        return User.objects.get(username=username)

    @sync_to_async
    def create_message(self, room, user, content):
        return Message.objects.create(room=room, user=user, content=content)

    @sync_to_async
    def get_initial_messages(self, room_name):
        room = Room.objects.get(name=room_name)
        messages = Message.objects.filter(room=room).order_by('timestamp')
        return [{
            'user': message.user.username,
            'content': message.content,
            'timestamp': message.timestamp.isoformat()
        } for message in messages]

    async def update_contacts(self, room):
        participants = await sync_to_async(lambda: list(room.participants.all()))()
        for participant in participants:
            contacts = await sync_to_async(self.get_contacts)(participant)
            await self.channel_layer.group_send(
                f"contacts_group_{participant.username}",
                {
                    "type": "update_contacts",
                    "contacts": contacts
                }
            )

    def get_contacts(self, user):
        rooms = Room.objects.filter(participants=user).distinct()
        contacts = set()
        for room in rooms:
            for participant in room.participants.all():
                if participant != user:
                    contacts.add(participant)
        return [{"pk": contact.pk, "username": contact.username} for contact in contacts]
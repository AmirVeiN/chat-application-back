import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Room, Message
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from django.db.models import Q
User = get_user_model()

class BaseConnection:
    
    @staticmethod
    @sync_to_async
    def get_contacts(user):
        rooms = Room.objects.filter(participants=user).distinct()
        contacts = set()
        for room in rooms:
            for participant in room.participants.all():
                if participant != user:
                    unread_count = Message.objects.filter(room=room, user=participant, read=False).count()
                    contacts.add((participant, unread_count))
        return [
            {"pk": contact.id, "username": contact.username, "online": contact.online, "unread_count": unread_count}
            for contact, unread_count in contacts
        ]
    
    @staticmethod
    async def update_contacts_for_all_users(user, channel_layer):
        rooms = await sync_to_async(lambda: list(Room.objects.filter(participants=user).distinct()))()
        for room in rooms:
            participants = await sync_to_async(lambda: list(room.participants.all()))()
            for participant in participants:
                contacts = await BaseConnection.get_contacts(participant)
                await channel_layer.group_send(
                    f"contacts_group_{participant.username}",
                    {
                        "type": "update_contacts",
                        "contacts": contacts
                    }
                )

class ContactsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_anonymous:
            await self.close()
        else:
            await self.set_user_online_status(True)
            self.group_name = f"contacts_group_{self.user.username}"
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            await BaseConnection.update_contacts_for_all_users(self.user, self.channel_layer)
            if self.user.role == 4:
                rooms = await self.get_rooms_and_consultants_for_consultant()
                await self.send(text_data=json.dumps({
                    'type': 'update_rooms',
                    'rooms': rooms
                }))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            await self.set_user_online_status(False)
            await BaseConnection.update_contacts_for_all_users(self.user, self.channel_layer)

    async def update_contacts(self, event):
        contacts = event['contacts']
        await self.send(text_data=json.dumps({
            'type': 'update_contacts',
            'contacts': contacts
        }))

    @sync_to_async
    def set_user_online_status(self, is_online):
        self.user.online = is_online
        self.user.save()
    
    @database_sync_to_async
    def get_rooms_and_consultants_for_consultant(self):
        consultant_rooms = Room.objects.filter(
            Q(participants__in=self.user.consultants.all())
        ).distinct()

        rooms_data = []
        for room in consultant_rooms:
            participants = room.participants.all()
            participants_data = [
                {
                    'id': participant.id,
                    'username': participant.username,
                    'fullname': participant.fullname,
                    'role': participant.role,
                    'status': participant.status,
                } for participant in participants
            ]
            rooms_data.append({
                'id': room.id,
                'name': room.name,
                'participants': participants_data
            })

        consultants = self.user.consultants.all()
        consultants_data = [
            {
                'id': consultant.id,
                'username': consultant.username,
                'fullname': consultant.fullname,
                'role': consultant.role,
                'status': consultant.status,
            } for consultant in consultants
        ]

        return {
            'rooms': rooms_data,
            'consultants': consultants_data
        }

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # ارسال پیام‌های اولیه در بسته‌های 20 تایی
        messages = await self.get_paginated_messages(self.room_name, 20, 0)
        await self.send(text_data=json.dumps({
            "type": "initial_messages",
            "messages": messages
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type", None)

        if message_type == "message_read":
            message_id = data["message_id"]
            await self.message_read({"message_id": message_id})
        elif message_type == "chat_message":
            if "message" in data and "username" in data:
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
                            "id": msg.id,
                            "user": user.username,
                            "content": msg.content,
                            'timestamp': msg.timestamp.isoformat(),
                            'read': msg.read
                        },
                    },
                )
            else:
                print("Invalid message format:", data)
        elif message_type == "load_more_messages":
            offset = data.get("offset", 0)
            messages = await self.get_paginated_messages(self.room_name, 20, offset)
            await self.send(text_data=json.dumps({
                "type": "more_messages",
                "messages": messages
            }))
        else:
            print("Unknown message type:", data)

    async def chat_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": message
        }))

    async def message_read(self, event):
        message_id = event["message_id"]
        await self.mark_message_as_read(message_id)
            
        room = await self.get_room(self.room_name)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "message_read_update",
                "message_id": message_id
            },
        )

    async def message_read_update(self, event):
        message_id = event["message_id"]
        await self.send(text_data=json.dumps({
            "type": "message_read_update",
            "message_id": message_id
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
    def get_paginated_messages(self, room_name, limit, offset):
        room = Room.objects.get(name=room_name)
        messages = Message.objects.filter(room=room).order_by('-timestamp')[offset:offset + limit]
        return [{
            'id': message.id,
            'user': message.user.username,
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
            'read': message.read
        } for message in messages]

    async def mark_message_as_read(self, message_id):
        message = await sync_to_async(Message.objects.get)(id=message_id)
        message.read = True
        await sync_to_async(message.save)()

        room = await sync_to_async(lambda: message.room)()
        participants = await sync_to_async(lambda: list(room.participants.all()))()
        for participant in participants:
            contacts = await BaseConnection.get_contacts(participant)
            await self.channel_layer.group_send(
                f"contacts_group_{participant.username}",
                {
                    "type": "update_contacts",
                    "contacts": contacts
                }
            )

    async def update_contacts(self, room):
        participants = await sync_to_async(lambda: list(room.participants.all()))()
        for participant in participants:
            contacts = await BaseConnection.get_contacts(participant)
            await self.channel_layer.group_send(
                f"contacts_group_{participant.username}",
                {
                    "type": "update_contacts",
                    "contacts": contacts
                }
            )

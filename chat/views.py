from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from user.models import UsersData
from user.serializers import UserSerializer
from .models import Room, Message
from .serializers import RoomSerializer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class CreateOrJoinRoomView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')

        if not username:
            return Response({'error': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = UsersData.objects.get(username=username)
        except UsersData.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        local_username = request.user.username
        room_name = "_".join(sorted([local_username, username]))

        room, created = Room.objects.get_or_create(name=room_name)
        room.participants.add(request.user)
        room.participants.add(user)
        room.save()

        return Response(RoomSerializer(room).data, status=status.HTTP_200_OK)

    def get_contacts(self, user):
        rooms = Room.objects.filter(participants=user).distinct()
        contacts = set()
        for room in rooms:
            for participant in room.participants.all():
                if participant != user:
                    contacts.add(participant)
        return [{"pk": contact.pk, "username": contact.username} for contact in contacts]

    def room_has_messages(self, room):
        return Message.objects.filter(room=room).exists()

class GetContactsView(APIView):
    def get(self, request):
        rooms = Room.objects.filter(participants=request.user).distinct()
        contacts = set()

        for room in rooms:
            for participant in room.participants.all():
                if participant != request.user:
                    contacts.add(participant)

        serializer = UserSerializer(list(contacts), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
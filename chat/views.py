from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from user.models import UsersData
from user.serializers import UserSerializer
from .models import Room, Message,UploadedFile
from .serializers import RoomSerializer,UploadedFileSerializer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.permissions import IsAuthenticated

class CreateOrJoinRoomView(APIView):
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        
        username = request.data.get('username')
        consultant = request.data.get('consultant')
    
        if not username:
            return Response({'error': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if consultant and request.user.role == 4 :
            
            if not consultant:
                return Response({'error': 'consultant is required'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = UsersData.objects.get(username=username)
            except UsersData.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            local_username = consultant
            room_name = "_".join(sorted([local_username, username]))

            room, created = Room.objects.get_or_create(name=room_name)
            room.participants.add(request.user)
            room.participants.add(user)
            room.save()

            return Response(RoomSerializer(room).data, status=status.HTTP_200_OK)
            
        else :
        
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
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        rooms = Room.objects.filter(participants=request.user).distinct()
        contacts = set()

        for room in rooms:
            for participant in room.participants.all():
                if participant != request.user:
                    contacts.add(participant)

        serializer = UserSerializer(list(contacts), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        serializer = UploadedFileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
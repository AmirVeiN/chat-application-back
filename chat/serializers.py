from rest_framework import serializers
from user.serializers import UserSerializer
from .models import Room, Message


class RoomSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True)

    class Meta:
        model = Room
        fields = ["id", "name", "participants"]


class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Message
        fields = ["id", "user", "content", "timestamp"]

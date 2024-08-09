from rest_framework import serializers
from user.serializers import UserSerializer
from .models import Room, Message,UploadedFile


class RoomSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True)

    class Meta:
        model = Room
        fields = ["id", "name", "participants"]


class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Message
        fields = ["id", "user", "content", "timestamp", "read"]

class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['file']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)
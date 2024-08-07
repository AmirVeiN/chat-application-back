from rest_framework import serializers
from .models import UsersData
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersData
        fields = [
            "pk",
            "username",
            "fullname",
            "role",
            "status",
            "updated_at",
            "online",
            "created_at",
        ]

class RegisterSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = UsersData
        fields = ['username', 'fullname', 'role', 'password']

    def create(self, validated_data):
        user = UsersData(
            username=validated_data['username'],
            fullname=validated_data['fullname'],
            role=validated_data['role']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
    

class CustomTokenObtainPairSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(username=username, password=password)

        if user is None:
            raise serializers.ValidationError('Invalid credentials')

        refresh = RefreshToken.for_user(user)
        return {
            'username': username,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
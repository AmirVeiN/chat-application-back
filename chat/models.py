from user.models import UsersData
from django.utils import timezone
from django.db import models


class Room(models.Model):
    name = models.CharField(max_length=255, unique=True)
    participants = models.ManyToManyField(UsersData)

    def __str__(self):
        return f"{self.pk} - {self.name}" 

class Message(models.Model):
    room = models.ForeignKey(Room, related_name="messages", on_delete=models.CASCADE)
    user = models.ForeignKey(UsersData, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.room} - {self.user} - {self.content}" 
    
class UploadedFile(models.Model):
    user = models.ForeignKey(UsersData, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.file.name}"
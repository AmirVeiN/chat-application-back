from .constants import USER_TYPE_CHOICES
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings

class CustomUserManager(BaseUserManager):
    def create_user(self, username, fullname, role, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, fullname=fullname, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, fullname, role, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, fullname, role, password, **extra_fields)
    

class UsersData(AbstractBaseUser, PermissionsMixin):
    
    username = models.CharField(max_length=100, unique=True)
    fullname = models.CharField(max_length=100)
    role = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES)
    status = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    online = models.BooleanField(default=False)
    consultants = models.ManyToManyField(to=settings.AUTH_USER_MODEL, related_name='consulted_users', null=True, blank=True)
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['fullname', 'role']

    def __str__(self):
        return self.username
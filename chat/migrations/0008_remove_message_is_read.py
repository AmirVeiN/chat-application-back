# Generated by Django 5.0.7 on 2024-08-06 07:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0007_message_is_read_alter_message_timestamp'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='is_read',
        ),
    ]
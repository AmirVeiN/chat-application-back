# Generated by Django 5.0.7 on 2024-08-05 08:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_contact'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Contact',
        ),
    ]

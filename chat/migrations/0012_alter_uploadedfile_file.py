# Generated by Django 5.0.7 on 2024-08-09 08:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0011_alter_uploadedfile_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uploadedfile',
            name='file',
            field=models.FileField(upload_to='uploads/'),
        ),
    ]
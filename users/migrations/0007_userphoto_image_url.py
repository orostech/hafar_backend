# Generated by Django 5.1.5 on 2025-01-19 16:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_remove_profile_device_token_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userphoto',
            name='image_url',
            field=models.URLField(blank=True, null=True),
        ),
    ]

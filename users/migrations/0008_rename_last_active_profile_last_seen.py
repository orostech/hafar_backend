# Generated by Django 5.1.5 on 2025-01-23 12:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_userphoto_image_url'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='last_active',
            new_name='last_seen',
        ),
    ]

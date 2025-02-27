# Generated by Django 5.1.5 on 2025-02-22 22:03

import django_jsonform.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('config', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appconfiguration',
            name='data',
            field=django_jsonform.models.fields.JSONField(),
        ),
        migrations.AlterField(
            model_name='appmaintenance',
            name='message',
            field=models.TextField(default='Our app is currently undergoing maintenance to bring you an even better experience. We apologize for any inconvenience this may cause. Please check back later, and thank you for your patience!'),
        ),
    ]

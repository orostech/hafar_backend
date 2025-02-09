# Generated by Django 5.1.5 on 2025-02-02 08:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='is_pinned',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='message',
            name='reactions',
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='messagereaction',
            name='message',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='message_reactions', to='chat.message'),
        ),
    ]

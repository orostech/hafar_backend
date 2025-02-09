# Generated by Django 5.1.5 on 2025-01-15 14:14

import django.db.models.deletion
import django.utils.timezone
import users.models
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=150, null=True, unique=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('first_name', models.CharField(max_length=254)),
                ('last_name', models.CharField(max_length=254)),
                ('phone', models.CharField(blank=True, max_length=15)),
                ('email_verified', models.BooleanField(default=False)),
                ('phone_verified', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            managers=[
                ('objects', users.models.CustomUserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('display_name', models.CharField(max_length=20)),
                ('date_of_birth', models.DateField()),
                ('gender', models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], help_text='What gender do you want to match with?', max_length=1)),
                ('bio', models.TextField(blank=True)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
                ('user_type', models.CharField(choices=[('S', 'Standard'), ('P', 'Premium'), ('B', 'Business')], default='S', max_length=1)),
                ('relationship_goal', models.CharField(choices=[('LSR', 'Looking for Short-term Relationship'), ('LLR', 'Looking for Long-term Relationship'), ('LFR', 'Looking for Friendship'), ('LMR', 'Looking to Meet New People'), ('NSR', 'Not Sure Yet')], default='NSR', max_length=3)),
                ('interested_in', models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('E', 'Everyone')], default='E', max_length=6)),
                ('body_type', models.CharField(choices=[('SL', 'Slim'), ('AV', 'Average'), ('AT', 'Athletic'), ('CF', 'Curvy'), ('FF', 'Full Figure'), ('MS', 'Muscular'), ('OW', 'Overweight'), ('UN', 'Underweight'), ('OT', 'Other')], default='AV', max_length=2)),
                ('complexion', models.CharField(choices=[('FA', 'Fair'), ('LT', 'Light'), ('MD', 'Medium'), ('TN', 'Tan'), ('DR', 'Dark'), ('BR', 'Brown'), ('OL', 'Olive'), ('BK', 'Black'), ('OT', 'Other')], default='MD', max_length=2)),
                ('number_of_kids', models.PositiveIntegerField(blank=True, null=True)),
                ('do_you_have_pets', models.CharField(choices=[('Y', 'Yes, I have pets'), ('N', 'No, I don’t have pets'), ('D', 'I don’t like pets'), ('A', 'I would like to have pets one day')], default='D', max_length=1)),
                ('weight', models.PositiveIntegerField(blank=True, help_text='Weight in kilograms (kg)', null=True)),
                ('height', models.PositiveIntegerField(blank=True, help_text='Height in centimeters (cm)', null=True)),
                ('dietary_preferences', models.CharField(blank=True, choices=[('V', 'Vegetarian'), ('VN', 'Vegan'), ('GF', 'Gluten-Free'), ('DF', 'Dairy-Free'), ('P', 'Pescatarian'), ('OU', 'Other'), ('N', 'None')], max_length=2)),
                ('smoking', models.CharField(choices=[('Y', 'Yes, I smoke'), ('N', 'No, I don’t smoke'), ('S', 'Sometimes')], default='N', max_length=1)),
                ('drinking', models.CharField(choices=[('Y', 'Yes, I drink'), ('N', 'No, I don’t drink'), ('S', 'Sometimes')], default='N', max_length=1)),
                ('relationship_status', models.CharField(choices=[('S', 'Single'), ('R', 'In a Relationship'), ('M', 'Married'), ('D', 'Divorced'), ('NSR', 'Not Sure Yet')], default='NSR', max_length=3)),
                ('instagram_handle', models.CharField(blank=True, max_length=100, null=True)),
                ('facebook_link', models.URLField(blank=True, null=True)),
                ('last_active', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.PositiveSmallIntegerField(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('rated_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings_received', to='users.profile')),
                ('rating_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings_given', to='users.profile')),
            ],
            options={
                'unique_together': {('rated_user', 'rating_user')},
            },
        ),
    ]

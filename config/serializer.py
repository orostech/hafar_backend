# serializer.py
from rest_framework import serializers
from match.serializers import ProfileMinimalSerializer
from users.models import Profile, User
from users.serializers import ProfileSerializer
from .models import AppConfiguration, AppMaintenance
from django.contrib.auth.models import Group



class AppConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppConfiguration
        fields = ['config_type', 'platform', 'data', 'version', 'last_updated']
        read_only_fields = ['version', 'last_updated']


class MaintenanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppMaintenance
        fields = '__all__'


class DashboardMetricSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    pending_approval = serializers.IntegerField()
    new_users_today = serializers.IntegerField()
    # total_earnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_coins = serializers.IntegerField()
    matches_count = serializers.IntegerField()
    premium_matches = serializers.IntegerField()
    likes_count = serializers.IntegerField()
    super_likes_count = serializers.IntegerField()
    active_subscriptions = serializers.IntegerField()
    gift_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    subscription_revenue = serializers.DecimalField(
        max_digits=12, decimal_places=2)


class TrendMetricSerializer(serializers.Serializer):
    label = serializers.CharField()
    current = serializers.IntegerField()
    previous = serializers.IntegerField()
    percentage_change = serializers.FloatField()
    trend_direction = serializers.CharField()


class ChartDataSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    datasets = serializers.DictField()


class AdminProfileSerializer(ProfileSerializer):
    class Meta(ProfileSerializer.Meta):
        fields = ProfileSerializer.Meta.fields + \
            tuple(['user_status', 'is_verified'])
        read_only_fields = ProfileSerializer.Meta.read_only_fields


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions']

class AdminProfileListSerializer(ProfileMinimalSerializer):
    id = serializers.ReadOnlyField(source='user.id')
    email = serializers.ReadOnlyField(source='user.email')
    profile_photo = serializers.ReadOnlyField(source='user.get_profile_photo')
    average_rating = serializers.ReadOnlyField(source='user.average_rating')
    created_at = serializers.ReadOnlyField(source='user.created_at')

    class Meta:
        model = Profile
        fields = ['id', 'email', 'display_name', 'profile_photo', 'created_at', 'average_rating', 'gender', 'state', 'country', 'user_status',
                  'online_status', 'is_premium', 'latlng'
                  ]


class AdminStaffSerializer(serializers.ModelSerializer):
    # id = serializers.ReadOnlyField(source='user.id')
    # email = serializers.ReadOnlyField(source='user.email')
    profile_photo = serializers.ReadOnlyField(source='get_profile_photo')
    display_name = serializers.ReadOnlyField(source='username')
    groups = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), many=True)
    class Meta:
        model = User
        fields = ['id', 'email', 'profile_photo', 'display_name', 'is_staff', 'is_superuser', 'groups']
        read_only_fields = ['id', 'email','is_staff', 'is_superuser', 'groups']

class AdminProfileSerializer(serializers.ModelSerializer):
    user = AdminStaffSerializer()
    class Meta:
        model = Profile
        fields = '__all__'

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user

        # Update User fields (is_staff, groups)
        user.is_staff = user_data.get('is_staff', user.is_staff)
        user.is_superuser = user_data.get('is_superuser', user.is_superuser)
        if 'groups' in user_data:
            user.groups.set(user_data['groups'])
        user.save()

        # Update Profile fields
        return super().update(instance, validated_data)
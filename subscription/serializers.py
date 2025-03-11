from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription

class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = serializers.StringRelatedField()
    
    class Meta:
        model = UserSubscription
        fields = ['id', 'plan', 'start_date', 'end_date', 'is_active']
        read_only_fields = ['start_date', 'end_date', 'is_active']

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField()
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name','title','description','iap_apple_id','iap_google_id', 'coin_price','amount', 'duration_days']

    def get_amount(self, obj):
        return obj.get_naira_amount()
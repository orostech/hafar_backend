from rest_framework.viewsets import ReadOnlyModelViewSet
from users.const import *
from wallet.models import CoinRate
from wallet.serializers import CoinRateSerializer
from .models import AppConfiguration
from .serializer import AppConfigurationSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from subscription.models import SubscriptionPlan
from subscription.serializers import SubscriptionPlanSerializer


class ConfigurationViewSet(ReadOnlyModelViewSet):
    queryset = AppConfiguration.objects.filter(is_active=True)
    serializer_class = AppConfigurationSerializer

    @action(detail=False, methods=['get'])
    def initial_load(self, request):      
        config_data = {
            'app_version': {
            'min_supported': '1.0.0',
            'latest': '1.0.0',
            'force_update': False
            },
            'choices': {
            'account_status': self._format_choices(ACCOUNT_STATUS_CHOICES),
            'visibility': self._format_choices(VISIBILITY_CHOICES),
            'verification_status': self._format_choices(VERIFICATION_STATUS_CHOICES)
            },
            'defaults': {
            'max_photos': 9,
            'max_interests': 5,
            'min_age': 18,
            'max_age': 100,
            'default_radius': 100,
            },
            'feature_flags': {
            'allow_deposit': True,
            'allow_withdrawal': True,
            'allow_coin_transfer': True,
            'allow_referral_bonus': True,
            }
        }
        config_data['coinrate'] =  CoinRateSerializer(CoinRate.objects.filter(is_active=True).latest('created_at')).data
        config_data['subscription_plans'] = SubscriptionPlanSerializer(SubscriptionPlan.objects.filter(is_active=True),many=True).data

        return Response(config_data)

    def _format_choices(self, choices):
        return [{'code': code, 'label': label} for code, label in choices]

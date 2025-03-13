from rest_framework.viewsets import ReadOnlyModelViewSet
from users.const import *
from wallet.models import CoinRate
from wallet.serializers import CoinRateSerializer
from .models import AppConfiguration, AppMaintenance
from .serializer import AdminProfileSerializer,AdminProfileListSerializer, AppConfigurationSerializer, MaintenanceSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from subscription.models import SubscriptionPlan
from subscription.serializers import SubscriptionPlanSerializer
from rest_framework import viewsets
from users.models import  Profile
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
# from .serializers import AdminProfileSerializer
from .permissions import IsAdminUser


class ConfigurationViewSet(ReadOnlyModelViewSet):
    queryset = AppConfiguration.objects.filter(is_active=True)
    serializer_class = AppConfigurationSerializer

    @action(detail=False, methods=['get'])
    def initial_load(self, request):
        config = self._get_configurations(),
        response_data = {
            'app_versions': config[0].get('app_versions', {}),
            # 'app_config': self._get_configurations(),
            'maintenance': self._get_maintenance_info(),
            'subscription_plans': self._get_subscription_plans(),
            'coin_rate': self._get_coin_rate(),
           
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

        response_data[ 'choices'] =  {
            'account_status': self._format_choices(ACCOUNT_STATUS_CHOICES),
            'visibility': self._format_choices(VISIBILITY_CHOICES),
            'verification_status': self._format_choices(VERIFICATION_STATUS_CHOICES)
            },
        
        # response_data['app_versions'] =
        
    
        return Response(response_data)
    
    def _get_configurations(self):
        configs = {}
        # print(len(self.queryset))
        for entry in self.queryset:
            platform = entry.platform if entry.platform != 'all' else 'global'
            config_type = entry.config_type
            if config_type not in configs:
                # print(config_type)
                configs[config_type] = {}
                # print(data)
            if entry.is_secret:
                pass
                # data = entry.encrypted_data
            else:
                data = entry.data
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, str):
                            if value.lower() == 'true':
                                data[key] = True
                            elif value.lower() == 'false':
                                data[key] = False
                            elif value.startswith('[') and value.endswith(']'):
                                try:
                                    data[key] = eval(value)
                                except:
                                    pass
                            elif value.isdigit():
                                data[key] = int(value)
            configs[config_type][platform] = data
        return configs

    def _get_maintenance_info(self):
        maintenance = AppMaintenance.objects.filter(is_active=True)[:3]
        return MaintenanceSerializer(maintenance, many=True).data

    def _get_subscription_plans(self):
        plans = SubscriptionPlan.objects.filter(is_active=True)
        return SubscriptionPlanSerializer(plans, many=True).data

    def _get_coin_rate(self):
        return CoinRateSerializer(CoinRate.objects.latest('created_at')).data

    # @action(detail=False, methods=['get'])
    # def initial_load(self, request):      
    #     config_data = {
    #         'app_version': {
    #         'min_supported': '1.0.0',
    #         'latest': '1.0.0',
    #         'force_update': False
    #         },
    #         'choices': {
    #         'account_status': self._format_choices(ACCOUNT_STATUS_CHOICES),
    #         'visibility': self._format_choices(VISIBILITY_CHOICES),
    #         'verification_status': self._format_choices(VERIFICATION_STATUS_CHOICES)
    #         },
    #         'defaults': {
    #         'max_photos': 9,
    #         'max_interests': 5,
    #         'min_age': 18,
    #         'max_age': 100,
    #         'default_radius': 100,
    #         },
    #         'feature_flags': {
    #         'allow_deposit': True,
    #         'allow_withdrawal': True,
    #         'allow_coin_transfer': True,
    #         'allow_referral_bonus': True,
    #         }
    #     }
    #     config_data['coinrate'] =  CoinRateSerializer(CoinRate.objects.filter(is_active=True).latest('created_at')).data
    #     config_data['subscription_plans'] = SubscriptionPlanSerializer(SubscriptionPlan.objects.filter(is_active=True),many=True).data

    #     return Response(config_data)

    def _format_choices(self, choices):
        return [{'code': code, 'label': label} for code, label in choices]




class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.select_related('user')
    serializer_class = AdminProfileListSerializer
    # AdminProfileSerializer
    # permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['user__email', 'display_name'
                    #  , 
                    #  'profession', 'address', 'state', 'country'
                     ]
    filterset_fields = [
        'gender',  'user_status', 'created_at'
        # 'user_type',
        # 'is_verified',
        # 'profile_visibility',
        # 'relationship_goal',
        # 'interested_in',
        # 'body_type',
        # 'complexion',
        # 'relationship_status',
        # 'selected_country',
        # 'selected_state'
    ]

  
    # class UserFilter(filters.FilterSet):
    #     start_date = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    #     end_date = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    #     class Meta:
    #         model = Profile
    #         fields = ['gender', 'user_status', 'start_date', 'end_date']

    def get_queryset(self):
        queryset = super().get_queryset()
        print(self.request.query_params)
        gender = self.request.query_params.get('gender', None)
        user_status = self.request.query_params.get('user_status', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        # user_type = self.request.query_params.get('user_type', None)
        # verification_status = self.request.query_params.get('verification_status', None)
        # country = self.request.query_params.get('country', None)
        if start_date and end_date:
            queryset = queryset.filter(created_at__range=[start_date, end_date])      
        if gender:
            queryset = queryset.filter(gender=gender) 
        if user_status:
            queryset = queryset.filter(user_status=user_status)
        # if user_type:
        #     queryset = queryset.filter(user_type=user_type)
        # if verification_status:
        #     queryset = queryset.filter(is_verified=verification_status)
        # if country:
        #     queryset = queryset.filter(selected_country=country)
        
        return queryset
    
    def get_serializer_class(self):
        serializer = super().get_serializer_class()
        if self.action == 'list':
            return AdminProfileListSerializer
        return serializer

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        user = self.get_object().user
        new_password = request.data.get('new_password')
        user.set_password(new_password)
        user.save()
        return Response({'status': 'password reset'})
    
  
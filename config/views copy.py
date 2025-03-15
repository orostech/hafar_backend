from rest_framework.viewsets import ReadOnlyModelViewSet
from gift.models import VirtualGift
from users.const import *
from users.serializers import LoginSerializer
from wallet.models import CoinRate, PaymentTransaction, Wallet
from wallet.serializers import CoinRateSerializer
from .models import AppConfiguration, AppMaintenance
from .serializer import AdminProfileSerializer, AdminProfileListSerializer, AppConfigurationSerializer, MaintenanceSerializer, DashboardMetricSerializer, TrendMetricSerializer, ChartDataSerializer, AdminProfileSerializer, GroupSerializer, AdminStaffSerializer

from rest_framework.decorators import action
from rest_framework.response import Response
from subscription.models import SubscriptionPlan, UserSubscription
from subscription.serializers import SubscriptionPlanSerializer
from rest_framework import viewsets,views,  filters, status
from users.models import Profile
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import FilterSet, DateTimeFilter,DateFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from match. models import Boost, Match, Like
from .permissions import IsAdminUser
from django.contrib.auth.models import Group


class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.select_related(
        'user').filter(user__is_staff=True)
    serializer_class = AdminProfileSerializer
    permission_classes = [IsAdminUser]
    # ... keep existing filter and search fields ...


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAdminUser]


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

        response_data['choices'] = {
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

    def _format_choices(self, choices):
        return [{'code': code, 'label': label} for code, label in choices]

class UserFilter(FilterSet):
    # start_date = DateTimeFilter(field_name='created_at', lookup_expr='gte')
    # end_date = DateTimeFilter(field_name='created_at', lookup_expr='lte')
    start_date = DateFilter(field_name='created_at', lookup_expr='gte')
    end_date = DateFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Profile
        fields = ['gender', 'user_status', 'start_date', 'end_date']

class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.select_related('user')
    serializer_class = AdminProfileListSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = UserFilter
    search_fields = ['user__email', 'display_name']
    # queryset = Profile.objects.select_related('user')
    # serializer_class = AdminProfileListSerializer
    # # AdminProfileSerializer
    # permission_classes = [IsAdminUser]
    # filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    # search_fields = ['user__email', 'display_name' ]
    # filterset_fields = [
    #     'gender',  'user_status', 'created_at'
    #     # 'user_type',
    #     # 'is_verified',
    #     # 'profile_visibility',
    #     # 'relationship_goal',
    #     # 'interested_in',
    #     # 'body_type',
    #     # 'complexion',
    #     # 'relationship_status',
    #     # 'selected_country',
    #     # 'selected_state'
    # ]

    # # class UserFilter(filters.FilterSet):
    # #     start_date = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    # #     end_date = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    # #     class Meta:
    # #         model = Profile
    # #         fields = ['gender', 'user_status', 'start_date', 'end_date']

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset
    #     print(self.request.query_params)
    #     gender = self.request.query_params.get('gender', None)
    #     user_status = self.request.query_params.get('user_status', None)
    #     start_date = self.request.query_params.get('start_date', None)
    #     end_date = self.request.query_params.get('end_date', None)

    #     # user_type = self.request.query_params.get('user_type', None)
    #     # verification_status = self.request.query_params.get('verification_status', None)
    #     # country = self.request.query_params.get('country', None)
    #     print(timezone.now().date())
    #     if start_date and end_date:
    #         queryset = queryset.filter(
    #             created_at__range=[start_date, end_date])
    #     if gender:
    #         queryset = queryset.filter(gender=gender)
    #     if user_status:
    #         queryset = queryset.filter(user_status=user_status)
    #     # if user_type:
    #     #     queryset = queryset.filter(user_type=user_type)
    #     # if verification_status:
    #     #     queryset = queryset.filter(is_verified=verification_status)
    #     # if country:
    #     #     queryset = queryset.filter(selected_country=country)

    #     return queryset

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


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'])
    def metrics(self, request):
        # Core metrics calculation
        thirty_days_ago = timezone.now() - timedelta(days=30)

        metrics = {
            'total_users': Profile.objects.count(),
            'active_users': Profile.objects.filter(last_seen__gte=thirty_days_ago).count(),
            'pending_approval': Profile.objects.filter(user_status='PA').count,
            # 'new_users_today': Profile.objects.filter(created_at__date=timezone.now().date()).count(),
            'new_users_today': Profile.objects.filter(created_at__date=timezone.now().date()).count(),
            'total_coins': Wallet.objects.aggregate(total=Sum('balance'))['total'] or 0,
            'matches_count': Match.objects.count(),
            'premium_matches': Match.objects.filter(is_premium=True).count(),
            'likes_count': Like.objects.count(),
            'super_likes_count': Like.objects.filter(like_type='SUPER').count(),
            'active_subscriptions': UserSubscription.objects.filter(is_active=True).count(),
        }

        # # Financial calculations
        # payment_txns = PaymentTransaction.objects.filter(status='COMPLETED')
        # metrics['total_earnings'] = payment_txns.aggregate(total=Sum('naira_amount'))['total'] or 0

        # Gift revenue (10% platform fee)
        from decimal import Decimal
        total_gift_coins = VirtualGift.objects.aggregate(
            total=Sum('coins_value'))['total'] or 0
        metrics['gift_revenue'] = (Decimal(
            total_gift_coins) * Decimal('0.10')) / CoinRate.objects.latest('created_at').rate

        # Subscription revenue
        active_subs = UserSubscription.objects.filter(is_active=True)
        metrics['subscription_revenue'] = sum(
            sub.plan.get_naira_amount() for sub in active_subs
            # if sub.purchase_method == 'COINS'
        )

        return Response(DashboardMetricSerializer(metrics).data)

    @action(detail=False, methods=['get'])
    def trends(self, request):
        def calculate_trend(current, previous):
            if previous == 0:
                return {'percentage_change': 100.0, 'trend': 'up'}
            change = ((current - previous) / previous) * 100
            return {
                'percentage_change': abs(round(change, 1)),
                'trend': 'up' if change > 0 else 'down'
            }

        # Date ranges
        current_start = timezone.now() - timedelta(days=7)
        previous_start = current_start - timedelta(days=7)

        # User trends
        current_users = Profile.objects.filter(
            created_at__gte=current_start).count()
        previous_users = Profile.objects.filter(
            created_at__gte=previous_start,
            created_at__lt=current_start
        ).count()
        user_trend = calculate_trend(current_users, previous_users)

        # Engagement trends
        current_likes = Like.objects.filter(
            created_at__gte=current_start).count()
        previous_likes = Like.objects.filter(
            created_at__gte=previous_start,
            created_at__lt=current_start
        ).count()
        like_trend = calculate_trend(current_likes, previous_likes)

        # Financial trends
        current_revenue = PaymentTransaction.objects.filter(
            created_at__gte=current_start,
            status='COMPLETED'
        ).aggregate(total=Sum('naira_amount'))['total'] or 0

        previous_revenue = PaymentTransaction.objects.filter(
            created_at__gte=previous_start,
            created_at__lt=current_start,
            status='COMPLETED'
        ).aggregate(total=Sum('naira_amount'))['total'] or 0
        revenue_trend = calculate_trend(current_revenue, previous_revenue)

        trends = [
            {'label': 'New Users', **user_trend, 'current': current_users},
            {'label': 'Engagement', **like_trend, 'current': current_likes},
            {'label': 'Revenue', **revenue_trend, 'current': current_revenue}
        ]

        return Response(TrendMetricSerializer(trends, many=True).data)

    @action(detail=False, methods=['get'])
    def charts(self, request):
        # User growth chart
        user_data = Profile.objects.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('user')
        ).order_by('date')
        if not user_data:
            chart_data['labels'] = []
        # Revenue breakdown
        from decimal import Decimal
        revenue_sources = {
            'subscriptions': sum(sub.plan.get_naira_amount() for sub in UserSubscription.objects.filter(is_active=True)),
            'gifts': (VirtualGift.objects.aggregate(total=Sum('coins_value'))['total'] or 0) * Decimal('0.10') / CoinRate.objects.latest().rate,
            # 'boosts': Boost.objects.aggregate(total=Sum('coin_cost'))['total'] or 0,
            # Assuming each boost costs 100 coins
            'boosts': Boost.objects.filter(is_active=True).count() * 100,
        }

        # # Format chart data
        # chart_data = {
        #     'user_growth': {
        #         'labels': [entry['date'].strftime('%Y-%m-%d') for entry in user_data],
        #         'datasets': {'label': 'New Users', 'data': [entry['count'] for entry in user_data]}
        #     },
        #     'revenue_breakdown': {
        #         'labels': list(revenue_sources.keys()),
        #         'datasets': {'label': 'Revenue', 'data': list(revenue_sources.values())}
        #     }
        # }
        chart_data = {
            # Ensure labels exist
            'labels': [entry['date'].strftime('%Y-%m-%d') for entry in user_data],
            'datasets': {
                'user_growth': {'label': 'New Users', 'data': [entry['count'] for entry in user_data]},
                'revenue_breakdown': {'label': 'Revenue', 'data': list(revenue_sources.values())}
            }
        }

        return Response(ChartDataSerializer(chart_data).data)



class AdminLoginView(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LoginSerializer


    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = [AllowAny]
        elif self.request.method == 'GET':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LoginSerializer
        return AdminStaffSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            user = authenticate(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )

            if user:
                if (user.is_staff or user.is_superuser):     
                    refresh = RefreshToken.for_user(user)
                    try:
                        profile_data = AdminStaffSerializer(user).data
                        return Response({
                            'refresh': str(refresh),
                            'access': str(refresh.access_token),
                            **profile_data
                        })
                    except:
                        return Response({
                            'error': 'Invalid credentials'
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                return Response({
                    'error': 'You are not authorized as Hafar staff'
                }, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
   
    # this will return the current admin profile
    def get(self, request):
        user = request.user
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            profile_data = AdminStaffSerializer(user).data
            return Response(profile_data)
        return Response({'error': 'You are not authorized as Hafar staff'}, status=status.HTTP_401_UNAUTHORIZED)
from rest_framework import viewsets, status,views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from wallet.payment_handlers import FlutterwaveHandler
from .models import SubscriptionPlan, UserSubscription
from .serializers import SubscriptionPlanSerializer, UserSubscriptionSerializer
from wallet.models import Transaction
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from google.oauth2 import service_account
from django.conf import settings
from googleapiclient.discovery import build
import time

def validate_platform_purchase(receipt_data, platform):
    """
    Validate in-app purchase receipts with platform APIs
    Returns (is_valid, error_message)
    """
    try:
        print('go 1')
        if platform == 'ANDROID':
            print('go 2')
            credentials = service_account.Credentials.from_service_account_info(
                # json.loads(settings.GOOGLE_SERVICE_ACCOUNT_JSON),
                 settings.FIREBASE_CONFIG,
                scopes=['https://www.googleapis.com/auth/androidpublisher']
            )
            print('go 3')
            android_publisher = build('androidpublisher', 'v3', credentials=credentials)
            # Verify subscription
            print('go 4')
            # print(receipt_data)
            result = android_publisher.purchases().subscriptionsv2().get(
                packageName= settings.APP_PACKAGE_NAME,
                token=receipt_data['purchaseToken']
            ).execute()
            print(result)

            print('go 5')
            # Check subscription status
            if result.get('subscriptionState') != 'SUBSCRIPTION_STATE_ACTIVE':
                return False, 'Subscription not active'

            print('go 6')
            # Check expiration
            expiry_time = int(result['lineItems'][0]['expiryTime'])
            if expiry_time < int(time.time() * 1000):
                return False, 'Subscription expired'

            return True, None

        elif platform == 'IOS':
            # Apple App Store validation
            validation_url = 'https://buy.itunes.apple.com/verifyReceipt' if settings.PRODUCTION else 'https://sandbox.itunes.apple.com/verifyReceipt'
            
            payload = {
                'receipt-data': receipt_data,
                'password': settings.APPLE_SHARED_SECRET,
                'exclude-old-transactions': True
            }

            response = requests.post(validation_url, json=payload)
            result = response.json()

            if response.status_code != 200 or result['status'] != 0:
                return False, 'Invalid App Store receipt'

            latest_receipt = result['latest_receipt_info'][0]
            if int(latest_receipt['expires_date_ms']) < int(time.time() * 1000):
                return False, 'Subscription expired'

        else:
            return False, 'Invalid platform'

        return True, None

    except Exception as e:
        print(f"Purchase validation failed: {str(e)}")
        return False, 'Validation error'

def get_google_auth_token():
    """Get OAuth2 token for Google Play API"""
    from oauth2client.service_account import ServiceAccountCredentials
    
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        json.loads(settings.GOOGLE_SERVICE_ACCOUNT_JSON),
        scopes=['https://www.googleapis.com/auth/androidpublisher']
    )
    return credentials.get_access_token().access_token


class SubscriptionPaymentView(views.APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request={
            "type": "object",
            "properties": {
                "plan_id": {"type": "integer"},
                "payment_method": {"type": "string", "enum": ["IAP", "FLUTTERWAVE"]},
                "payment_data": {"type": "object"}  # For IAP receipt or Flutterwave data
            }
        }
    )
    def post(self, request):
        try:
            plan = SubscriptionPlan.objects.get(id=request.data['plan_id'], is_active=True)
            payment_method = request.data.get('payment_method', 'IAP')
            
            if payment_method == 'IAP':
                # Existing IAP validation
                is_valid, error_msg = validate_platform_purchase(
                    request.data['payment_data'], 
                    request.data.get('platform', 'ANDROID')
                )
                if not is_valid:
                    return Response({'error': error_msg}, status=400)
                
                platform = request.data.get('platform', 'ANDROID')
                subscription = UserSubscription.objects.create(
                    user=request.user,
                    plan=plan,
                    purchase_method='PLAY_STORE' if platform == 'ANDROID' else 'APP_STORE',
                    is_active=True
                )
                
            elif payment_method == 'FLUTTERWAVE':
                # Initialize Flutterwave payment
                handler = FlutterwaveHandler()
                payment_url = handler.initialize_subscription_payment(
                    user=request.user,
                    plan=plan
                )
                return Response({'payment_url': payment_url})
                
            return Response(UserSubscriptionSerializer(subscription).data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=400)






class SubscriptionVerifyPaymentView(views.APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        tx_ref = request.query_params.get('tx_ref')
        if not tx_ref:
            return Response({'error': 'Missing transaction reference'}, status=400)

        handler = FlutterwaveHandler()
        try:
            is_valid = handler.verify_payment(tx_ref)
            return Response({'status': 'success' if is_valid else 'failed'})
        except Exception as e:
            return Response({'error': str(e)}, status=400)








class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Active Subscription Plans",
        description="Retrieve a list of active subscription plans available for users.",
        responses={
            200: OpenApiResponse(
                response=SubscriptionPlanSerializer,
                description="Successfully retrieved active subscription plans.",
                examples=[
                    OpenApiExample(
                        "Example Response",
                        value=[
                            {
                                "id": 1,
                                "name": "Monthly",
                                "coin_price": 500,
                                "duration_days": 30
                            },
                            {
                                "id": 2,
                                "name": "Weekly",
                                "coin_price": 150,
                                "duration_days": 7
                            }
                        ],
                        response_only=True
                    )
                ]
            )
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class UserSubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserSubscription.objects.filter(user=self.request.user)

    @extend_schema(
        summary="Purchase Subscription",
        description="Allows a user to purchase a subscription plan using their coins.",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "plan_id": {
                        "type": "integer",
                        "example": 1
                    }
                },
                "required": ["plan_id"]
            }
        },
        responses={
            201: OpenApiResponse(
                description="Subscription activated successfully.",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"status": "Subscription activated"},
                        response_only=True
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Insufficient coins or subscription activation failed.",
                examples=[
                    OpenApiExample(
                        "Error",
                        value={"error": "Insufficient coins or subscription failed"},
                        response_only=True
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Invalid subscription plan.",
                examples=[
                    OpenApiExample(
                        "Error",
                        value={"error": "Invalid subscription plan"},
                        response_only=True
                    )
                ]
            ),
        }
    )

    @action(detail=False, methods=['post'])
    def purchase(self, request):
        plan_id = request.data.get('plan_id')
        print(plan_id)
        try:
            print('me 1')
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
            print(plan)
            if request.user.activate_subscription(plan):
                # Create transaction record
                Transaction.objects.create(
                    user=request.user,
                    amount=plan.coin_price,
                    transaction_type='SPEND',
                    description=f"Premium subscription: {plan.name}"
                )
                return Response(
                    {'status': 'Subscription activated'},
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'error': 'Insufficient coins or subscription failed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {'error': 'Invalid subscription plan'},
                status=status.HTTP_404_NOT_FOUND
            )
        
    @extend_schema(
        summary="Verify Platform Purchase",
        description="Verify and activate subscription from platform purchase",
        request={
            "application/json": {
                "properties": {
                    "plan_id": {"type": "integer"},
                    "receipt": {"type": "string"},
                    "platform": {"type": "string", "enum": ["ANDROID", "IOS"]}
                }
            }
        },
        responses={200: OpenApiResponse(...)}
    )

    @action(detail=False, methods=['post'])
    def verify_platform_purchase(self, request):
        try:
            plan = SubscriptionPlan.objects.get(id=request.data['plan_id'], is_active=True)
            receipt_data = request.data['receipt']
            platform = request.data['platform']
            is_valid, error_msg = validate_platform_purchase(receipt_data, platform)
            if is_valid:
                    subscription = UserSubscription.objects.create(
                        user=request.user,
                        plan=plan,
                        purchase_method='PLAY_STORE' if platform == 'ANDROID' else 'APP_STORE',
                        # start_date=timezone.now(),
                        # end_date=calculate_end_date(plan.duration_days),
                        is_active=True
                    )
                    return Response(UserSubscriptionSerializer(subscription).data, status=201)
                
            return Response({'error': error_msg}, status=400)
        
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Invalid plan'}, status=404)
        except KeyError as e:
            return Response({'error': f'Missing field: {str(e)}'}, status=400)
        
    @action(detail=False, methods=['post'])
    def create_subscription(self, request):
        try:
            plan = SubscriptionPlan.objects.get(id=request.data['plan_id'], is_active=True)
            platform = request.data.get('platform', 'ANDROID')
            purchase_method = request.data.get('purchase_method', 'COINS')
            
            subscription = UserSubscription.objects.create(
                user=request.user,
                plan=plan,
                purchase_method=purchase_method,
                is_active=True
            )
            
            return Response(
                UserSubscriptionSerializer(subscription).data,
                status=status.HTTP_201_CREATED
            )
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Invalid plan'}, status=404)
        except KeyError as e:
            return Response({'error': f'Missing field: {str(e)}'}, status=400)
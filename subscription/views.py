from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import SubscriptionPlan, UserSubscription
from .serializers import SubscriptionPlanSerializer, UserSubscriptionSerializer
from wallet.models import Transaction
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

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
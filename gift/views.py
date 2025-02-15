# views.py (gift app)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import GiftType, VirtualGift
from .serializers import GiftTypeSerializer, VirtualGiftSerializer, SendGiftSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample


class GiftShopAPI(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Available Gifts",
        description="Retrieve a list of all active gifts available in the shop, including their details such as name, price, image, and animation URLs.",
        responses={
            200: OpenApiResponse(
                response=GiftTypeSerializer(many=True),
                description="List of available gifts retrieved successfully.",
                examples=[
                    OpenApiExample(
                        "Example Response",
                        value=[
                            {
                                "id": 1,
                                "key": "rose",
                                "name": "Rose",
                                "coin_price": 10,
                                "image_url": "/media/gifts/images/rose.png",
                                "animation_url": "/media/gifts/animations/rose.mp4"
                            },
                            {
                                "id": 2,
                                "key": "diamond",
                                "name": "Diamond",
                                "coin_price": 120,
                                "image_url": "/media/gifts/images/diamond.png",
                                "animation_url": "/media/gifts/animations/diamond.mp4"
                            }
                        ],
                        response_only=True,
                    )
                ],
            ),
            401: OpenApiResponse(
                description="Unauthorized - User is not authenticated.",
                examples=[
                    OpenApiExample(
                        "Unauthorized",
                        value={
                            "detail": "Authentication credentials were not provided."},
                        response_only=True,
                    )
                ],
            ),
        },
    )
    def get(self, request):
        gifts = GiftType.objects.filter(is_active=True).order_by('coin_price')
        serializer = GiftTypeSerializer(gifts, many=True)
        return Response(serializer.data)


class SendGiftAPI(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Send a Gift",
        description="Allows an authenticated user to send a gift to another user. The sender's wallet will be debited, and the receiver's wallet will be credited with 90% of the gift's value.",
        request=SendGiftSerializer,
        responses={
            201: OpenApiResponse(
                response=VirtualGiftSerializer,
                description="Gift sent successfully.",
                examples=[
                    OpenApiExample(
                        "Example Response",
                        value={
                            "id": 1,
                            "gift_type": {
                                "id": 1,
                                "key": "rose",
                                "name": "Rose",
                                "coin_price": 10,
                                "image_url": "/media/gifts/images/rose.png",
                                "animation_url": "/media/gifts/animations/rose.mp4"
                            },
                            "message": "You're amazing!",
                            "coins_value": 10,
                            "timestamp": "2023-10-10T12:00:00Z",
                            "sender": "user1",
                            "receiver": "user2"
                        },
                        response_only=True,
                    )
                ],
            ),
            400: OpenApiResponse(
                description="Bad Request - Invalid input or insufficient coins.",
                examples=[
                    OpenApiExample(
                        "Invalid Input",
                        value={"error": "Invalid gift type or receiver."},
                        response_only=True,
                    ),
                    OpenApiExample(
                        "Insufficient Coins",
                        value={"error": "Insufficient coins to send gift."},
                        response_only=True,
                    ),
                ],
            ),
            401: OpenApiResponse(
                description="Unauthorized - User is not authenticated.",
                examples=[
                    OpenApiExample(
                        "Unauthorized",
                        value={
                            "detail": "Authentication credentials were not provided."},
                        response_only=True,
                    )
                ],
            ),
            404: OpenApiResponse(
                description="Not Found - Receiver or gift type not found.",
                examples=[
                    OpenApiExample(
                        "Receiver Not Found",
                        value={"error": "Receiver not found."},
                        response_only=True,
                    ),
                    OpenApiExample(
                        "Gift Type Not Found",
                        value={"error": "Invalid gift type."},
                        response_only=True,
                    ),
                ],
            ),
        },
    )
    def post(self, request):
        serializer = SendGiftSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            gift = VirtualGift.objects.create(
                sender=request.user,
                receiver=serializer.validated_data['receiver'],
                gift_type=serializer.validated_data['gift_type'],
                message=serializer.validated_data.get('message', '')
            )
            return Response(VirtualGiftSerializer(gift).data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {'error': 'Failed to send gift'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GiftHistoryAPI(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve Gift History",
        description="Retrieve a list of all gifts received by the authenticated user, including details about the sender, gift type, and timestamp.",
        responses={
            200: OpenApiResponse(
                response=VirtualGiftSerializer(many=True),
                description="Gift history retrieved successfully.",
                examples=[
                    OpenApiExample(
                        "Example Response",
                        value=[
                            {
                                "id": 1,
                                "gift_type": {
                                    "id": 1,
                                    "key": "rose",
                                    "name": "Rose",
                                    "coin_price": 10,
                                    "image_url": "/media/gifts/images/rose.png",
                                    "animation_url": "/media/gifts/animations/rose.mp4"
                                },
                                "message": "You're amazing!",
                                "coins_value": 10,
                                "timestamp": "2023-10-10T12:00:00Z",
                                "sender": "user1",
                                "receiver": "user2"
                            }
                        ],
                        response_only=True,
                    )
                ],
            ),
            401: OpenApiResponse(
                description="Unauthorized - User is not authenticated.",
                examples=[
                    OpenApiExample(
                        "Unauthorized",
                        value={
                            "detail": "Authentication credentials were not provided."},
                        response_only=True,
                    )
                ],
            ),
        },
    )
    def get(self, request):
        gifts = VirtualGift.objects.filter(
            receiver=request.user).select_related('gift_type')
        serializer = VirtualGiftSerializer(gifts, many=True)
        return Response(serializer.data)

from rest_framework import viewsets, permissions, status, views
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import FileUploadParser
from django.utils import timezone
from users.models import User
from .permissions import ChatPermissions
from .throttling import MessageRateThrottle
from .models import *
from .serializers import *
from django.core.exceptions import ValidationError
from match.models import Match
from django.contrib.postgres.search import SearchRank
from django.db.models import Q


class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSerializer
    # permission_classes = [permissions.IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated, ChatPermissions]

    def get_queryset(self):
        return Chat.objects.filter(
            models.Q(user1=self.request.user) |
            models.Q(user2=self.request.user)
        ).filter(is_active=True).prefetch_related('messages')

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        chat = self.get_object()
        if chat.user2 != request.user:
            return Response({'error': 'Not authorized'}, status=403)

        chat.is_accepted = True
        chat.requires_acceptance = False
        chat.save()
        return Response({'status': 'chat accepted'})

    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        chat = self.get_object()
        other_user = chat.user2 if chat.user1 == request.user else chat.user1

        # Create UserBlock
        UserBlock.objects.create(user=request.user, blocked_user=other_user)

        # Deactivate chat
        chat.is_active = False
        chat.save()
        return Response({'status': 'user blocked'})


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MiniMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [MessageRateThrottle]
    throttle_rates = {
        'message': '10/minute'  # Adjust based on your needs
    }

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):

        chatId = self.request.query_params.get(
            'chatId', None)
        if not chatId:
            raise ValidationError("chatId required")
        return Message.objects.filter(
            chat__id=chatId,
            deleted_for__isnull=True
        ).select_related('sender')
    
    def list(self, request, *args, **kwargs):
        # Mark all messages (except those sent by the current user) as read by setting read_at to now.
        self.get_queryset().exclude(sender=request.user).filter(read_at__isnull=True).update(read_at=timezone.now())
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        chat = Chat.objects.get(pk=self.kwargs['chat_pk'])
        serializer.save(sender=self.request.user, chat=chat)


class MessageRequestViewSet(viewsets.ModelViewSet):
    serializer_class = MessageRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MessageRequest.objects.filter(
            models.Q(sender=self.request.user) |
            models.Q(receiver=self.request.user)
        )

    @action(detail=False, methods=['get'])
    def pending(self, request):
        queryset = self.get_queryset().filter(models.Q(status='PENDING'),
                              models.Q(receiver=self.request.user))
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def sent(self, request):
        queryset = self.get_queryset().filter(models.Q(status='PENDING'),
                              models.Q(sender=self.request.user))
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        message_request = self.get_object()
        action = request.data.get('action')

        if message_request.receiver != request.user:
            return Response({'error': 'Not authorized'}, status=403)

        if action == 'accepted':
            chat = message_request.accept()
            return Response({
                        'type': 'CHAT',
                        'data': ChatSerializer(chat, context={'request': request}).data, }, status=status.HTTP_200_OK)
        
        elif action == 'rejected':
            message_request.reject()
        else:
            return Response({'error': 'Invalid action'}, status=400)

        return Response({'status': f'request {action}'})

    @action(detail=False, methods=['get'])
    def status(self, request):
        receiver_id = request.query_params.get('receiver_id')
        if not receiver_id:
            return Response({'error': 'receiver_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            message_request = MessageRequest.objects.get(
                (Q(sender=request.user, receiver_id=receiver_id) |
                 Q(sender=receiver_id, receiver_id=request.user))
            )

            if message_request.status == 'ACCEPTED':

                try:
                    chat = Chat.objects.filter(
                        (Q(user1=self.request.user), Q(user2_id=receiver_id)) |
                        (Q(user1_id=receiver_id), Q(user2=self.request.user))
                    ).filter(is_active=True)
                    return Response({
                        'type': 'CHAT',
                        'data': ChatSerializer(chat, context={'request': request}).data, }, status=status.HTTP_200_OK)

                except:
                    pass
            serializer = self.get_serializer(message_request)

            return Response({
                'type': 'NEW_REQUEST',
                'data': serializer.data, }, status=status.HTTP_200_OK)
        except MessageRequest.DoesNotExist:
            try:
                chat = Chat.objects.filter(
                    (Q(user1=request.user) & Q(user2_id=receiver_id)) |
                    (Q(user1_id=receiver_id) & Q(user2=request.user))
                ).filter(is_active=True).first()

                if chat:
                    return Response({
                        'type': 'CHAT',
                        'data': ChatSerializer(chat, context={'request': request}).data
                    }, status=status.HTTP_200_OK)
            except Chat.DoesNotExist:
                pass
            return Response({'type': 'no_request'}, status=status.HTTP_200_OK)




class MessageSearchView(views.APIView):
    def get(self, request):
        query = request.GET.get('q')
        chat_id = request.GET.get('chat_id')

        messages = Message.objects.filter(
            chat_id=chat_id,
            search_vector=query
        ).annotate(
            rank=SearchRank(models.F('search_vector'), query)
        ).order_by('-rank')

        return Response(MiniMessageSerializer(messages, many=True).data)


class SendInitialMessageView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        receiver_id = request.data.get('receiver_id')
        content = request.data.get('content')
        content_type = request.data.get('content_type', 'TEXT')

        try:
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        sender = request.user

        # Check existing chat
        chat = Chat.objects.filter(
            (Q(user1=sender, user2=receiver) | Q(user1=receiver, user2=sender))
        ).first()

        if chat:
            if chat.requires_acceptance and not chat.is_accepted:
                return Response({'error': 'Chat pending acceptance'}, status=status.HTTP_403_FORBIDDEN)
            # Send message via existing chat
            message = Message.objects.create(
                chat=chat,
                sender=sender,
                content=content,
                content_type=content_type
            )
            # serializer = MiniMessageSerializer(message)
            return Response({
                'type': 'CHAT',
                'chat': ChatSerializer(chat, context={'request': request}).data,
                'message': MiniMessageSerializer(message).data
            })
        else:
            match_exists = Match.objects.filter(
                (Q(user1=sender, user2=receiver) |
                 Q(user1=receiver, user2=sender)),
                is_active=True
            ).exists()

            if match_exists:
                chat = Chat.objects.create(
                    user1=sender,
                    user2=receiver,
                    requires_acceptance=False,
                    is_accepted=True
                )
                message = Message.objects.create(
                    chat=chat,
                    sender=sender,
                    content=content,
                    content_type=content_type
                )
                return Response({
                    'type': 'CHAT',
                    'chat': ChatSerializer(chat, context={'request': request}).data,
                    'message': MiniMessageSerializer(message).data
                })
            else:
                # Create message request
                message_request, created = MessageRequest.objects.get_or_create(
                    sender=sender,
                    receiver=receiver,
                    defaults={
                        'message': content,
                        'status': 'PENDING'
                    }
                )
                if created:
                    #    channel_layer = get_channel_layer()
                    #    async_to_sync(channel_layer.group_send)(
                    #         f'user_{receiver.id}',
                    #         {
                    #             'type': 'send_activity',
                    #             'action_type': 'message_request',
                    #             'data':  MessageRequestSerializer(message_request, context={'request': request} ).data
                    #         })
                    return Response({
                        'type': 'NEW_REQUEST',
                        'message_request': MessageRequestSerializer(message_request, context={'request': request}).data
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({'error': 'Request already sent'}, status=status.HTTP_400_BAD_REQUEST)


class MediaUploadView(views.APIView):
    parser_classes = [FileUploadParser]

    def post(self, request, format=None):
        file = request.data['file']
        # Validate file type and size
        if file.size > 10 * 1024 * 1024:  # 10MB
            return Response({'error': 'File too large'}, status=400)

        # Save to storage (e.g., S3)
        media_url = upload_to_storage(file)

        return Response({'url': media_url}, status=201)


def upload_to_storage(file):
    # Implement your storage logic here
    return f"https://storage.example.com/{file.name}"

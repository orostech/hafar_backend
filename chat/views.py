from rest_framework import viewsets, permissions, status,views
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import FileUploadParser
from .permissions import ChatPermissions
from .throttling import MessageRateThrottle
from .models import *
from .serializers import *
from django.core.exceptions import ValidationError
from match.models import Match
from django.contrib.postgres.search import  SearchRank

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
        print('me')
        chatId =self.request.query_params.get(
            'chatId', None)
        if not chatId:
            raise ValidationError("chatId required") 
        return Message.objects.filter(
            chat__id=chatId,
            # self.kwargs['chat_pk'],
            deleted_for__isnull=True
        ).select_related('sender')

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
        queryset = self.get_queryset().filter(status='PENDING')
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
           chat =  message_request.accept()
           serializer = ChatSerializer(chat, context={'request': request})
           return Response(serializer.data, status=status.HTTP_200_OK)
        elif action == 'rejected':
            message_request.reject()
        else:
            return Response({'error': 'Invalid action'}, status=400)
        
        return Response({'status': f'request {action}'})
    

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
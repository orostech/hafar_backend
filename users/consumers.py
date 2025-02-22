import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
from match.models import Match, Visit

class UserActivityConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.user = self.scope['user']
            if self.user.is_anonymous:
                await self.close()
            else:   
                    self.user_id = self.user.id 
                    self.room_group_name = f'user_{self.user_id}'
                    await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                    )
                    await self.accept()
                    await self.send_start_infos()
                

        except Exception as e:
            print(f"Error in WebSocket connection: {e}")
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def send_start_infos(self):
        # cart_count = await database_sync_to_async(self.get_cart_count)()
        # unread_notification_count = await self.get_unread_notification_count()
        # unread_messages_count = await database_sync_to_async(self.get_unread_messages_count)()

        await self.send(text_data=json.dumps({
            'action': 'initial_data',
            'new_likes': await self.get_new_likes(),
            'active_matches': await self.get_active_matches(),
            'recent_visitors': await self.get_recent_visitors(),
            'unread_notification_count': await self.get_unread_notification_count()
        }))
    async def send_activity(self, event):
        """Generic handler for all activity types"""
        print(event)
        await self.send(text_data=json.dumps({
            'action': event['action_type'],
            **event['data']
        }))
        
    async def profile_update(self, event):
        await self.send(text_data=json.dumps({
            'action': 'profile_update',
            'data': event['data']
        }))

    async def chat_update(self, data):
        await self.send(text_data=json.dumps({
            'action': 'chat_update',
            'chat': data['chat']
        }))

    # async def send_notification(self, data):
    #     await self.send(text_data=json.dumps({
    #         'action': 'notification',
    #         'data': data['content']
    #     }))

    @database_sync_to_async
    def get_unread_notification_count(self):
        return self.user.notifications.filter(read=False).count()
    
    @database_sync_to_async
    def get_new_likes(self):
        one_week_ago = timezone.now() - timedelta(days=7)
        return self.user.likes_received.filter(is_active=True,
            created_at__gte=one_week_ago).count()
    
    @database_sync_to_async
    def get_active_matches(self):
        return Match.objects.filter(
            Q(user1=self.user) | Q(user2=self.user),
            is_active=True
        ).count()
    
    
    @database_sync_to_async
    def get_recent_visitors(self):
        one_week_ago = timezone.now() - timedelta(days=7)
        return Visit.objects.filter(
            visited=self.user,
            created_at__gte=one_week_ago
        ).values('visitor').distinct().count()
    
    
    
from datetime import timezone
import json
from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Chat, Message, MessageReaction, PinnedMessage
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.db import models
from django.db.models import Q, F
from rest_framework.authtoken.models import Token

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:

            self.user = self.scope['user']
            if self.user.is_anonymous:
                await self.close()
            else:
                    self.chat_id = self.scope['url_route']['kwargs']['chat_id']
                    self.room_group_name = f'chat_{self.chat_id}'
               
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

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'message':
            await self.handle_message(data)
        elif action == 'typing':
            await self.handle_typing()
        elif action == 'reaction':
            await self.handle_reaction(data)
        elif action == 'toggle_pin':
            await self.handle_pin_message(data)
        elif action == 'read_receipt':
            await self.handle_read_receipt(data)

    async def handle_message(self, data):
        try:
            message = await self.create_message(data['content'], data.get('content_type', 'TEXT'))
            if message:
                # Immediate ACK with local ID
                await self.send(text_data=json.dumps({
                    'action': 'message_ack',
                    'local_id': data.get('local_id'),
                    'message_id': str(message.id),
                    'status': 'delivered'
                }))
                lastmessage = await self.message_to_json(message)
                # Broadcast to group
                await self.channel_layer.group_send( self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': lastmessage
                })
                # Broadcast chat update to both users' chat lists
                chat = await self.get_chat()
                for user in [chat.user1, chat.user2]:
                    await self.channel_layer.group_send(
                        f"user_{user.id}",
                        {
                            "type": "chat_update",
                            "chat": await self.chat_to_json(chat,lastmessage)
                        }
                    )
                
                # await self.notify_chat_list_update(message.chat)
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to send message',
                'error': str(e)
            }))

       # Add this new method
    async def notify_chat_list_update(self, chat):
        # Send update to both users' personal channels
        for user in [chat.user1, chat.user2]:
            await self.channel_layer.group_send(
                f"user_{user.id}_chats",
                {
                    'type': 'chat_updated',
                    'chat_id': str(chat.id),
                    'last_message': await self.message_to_json(chat.messages.last())
                }
            )
       # Add this new handler
    async def chat_updated(self, event):
        # This will be used for user-specific notifications
        await self.send(text_data=json.dumps({
            'action': 'chat_updated',
            'chat_id': event['chat_id'],
            'last_message': event['last_message']
        }))
    async def handle_typing(self):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': str(self.user.id)
            }
        )

    async def handle_reaction(self, data):
        try:
            message_id = data['message_id']
            emoji = data['emoji']
            user = self.scope['user']
            
            # Update database
            message, created = await self.update_reaction(message_id, user, emoji)
            
            # Broadcast update
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_reaction',
                    'message_id': str(message.id),
                    # 'reactions':message.reactions if message.reactions else {},
                    'emoji': emoji,
                    'user_id': str(user.id),
                    'action': 'add' if created else 'remove'
                }
            )
        except Exception as e:
            await self.send_error(str(e))

    async def handle_pin_message(self, data):
        try:
            message_id = data['message_id']
            is_pinned = data['is_pinned']
            user = self.scope['user']
            
            await self.toggle_pin_message(message_id, user, is_pinned)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_pinned',
                    'message_id': message_id,
                    'is_pinned': is_pinned,
                    'user_id': str(user.id)
                }
            )
        except Exception as e:
            await self.send_error(str(e))

    async def handle_read_receipt(self, data):
        message_id = data['message_id']
        await self.mark_message_read(message_id)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'read_receipt',
                'message_id': message_id,
                'user_id': str(self.user.id),
                'timestamp': str(timezone.now())
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'action': 'message',
            'message': event['message']
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'action': 'typing',
            'user_id': event['user_id']
        }))

    async def read_receipt(self, event):
        await self.send(text_data=json.dumps({
            'action': 'read_receipt',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp']
        }))
    async def message_reaction(self, event):
        await self.send(text_data=json.dumps({
            'action': 'reaction',
            'message_id': event['message_id'],
            'emoji': event['emoji'],
            'user_id': event['user_id'],
            'action_type': event['action']
        }))

    async def message_pinned(self, event):
        await self.send(text_data=json.dumps({
            'action': 'message_pinned',
            'message_id': event['message_id'],
            'is_pinned': event['is_pinned'],
            'user_id': event['user_id']
        }))

    async def send_start_infos(self):
        await self.send(text_data=json.dumps({
            'action': 'initial_data',
            'rate_user': await self.rate_user(),
        }))
        
    @database_sync_to_async
    def is_chat_member(self):
        return Chat.objects.filter(
            id=self.chat_id
        ).filter(models.Q(user1=self.user) | models.Q(user2=self.user)).exists()

    @database_sync_to_async
    def get_chat(self):
        return Chat.objects.get(id=self.chat_id)

    @database_sync_to_async
    def rate_user(self):
        chat = Chat.objects.get(id=self.chat_id)
        return chat.rate_user(self.user)
    

    @database_sync_to_async
    def create_message(self, content, content_type):
        chat = Chat.objects.get(id=self.chat_id)
        if chat.requires_acceptance and not chat.is_accepted:
            return None
        return Message.objects.create(
            chat=chat,
            sender=self.user,
            content=content,
            content_type=content_type
        )
    @database_sync_to_async
    def update_reaction(self, message_id, user, emoji):
        message = Message.objects.get(id=message_id)
        reaction, created = MessageReaction.objects.update_or_create(
            message=message,
            user=user,
            defaults={'emoji': emoji}
        )
        return reaction, created

    @database_sync_to_async
    def toggle_pin_message(self, message_id, user, is_pinned):
        message = Message.objects.get(id=message_id)
        if is_pinned:
            PinnedMessage.objects.get_or_create(message=message, user=user)
        else:
            PinnedMessage.objects.filter(message=message, user=user).delete()
        return is_pinned

    @database_sync_to_async
    def mark_message_read(self, message_id):
        message = Message.objects.get(id=message_id)
        if message.chat.get_other_user(message.sender) == self.user:
            message.mark_as_read(self.user)

    @database_sync_to_async
    def message_to_json(self, message):
        return {
            'id': str(message.id),
            'sender': str(message.sender.id),
            'content': message.content,
            'content_type': message.content_type,
            'timestamp': str(message.created_at),
            'read': bool(message.read_at)
        }
    
    @database_sync_to_async
    def chat_to_json(self, chat, lastmessage):
        return {
            'id': str(chat.id),
            'last_message': lastmessage,
            # chat.messages.last().content if chat.messages.exists() else None,
            'last_activity': str(chat.last_activity),
            # 'unread_count': 0
            # chat.messages.filter(read_at__isnull=True).exclude(sender=self.user).count()
        }
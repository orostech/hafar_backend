import json
from channels.generic.websocket import AsyncWebsocketConsumer

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
                

        except Exception as e:
            print(f"Error in WebSocket connection: {e}")
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    async def chat_update(self, data):
        await self.send(text_data=json.dumps({
            'action': 'chat_update',
            'chat': data['chat']
        }))

    async def send_notification(self, data):
        await self.send(text_data=json.dumps({
            'action': 'notification',
            'data': data['content']
        }))

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import ChatMessage
from workspaces.models import Workspace, WorkspaceMember

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.workspace_id = self.scope['url_route']['kwargs']['workspace_id']
        self.room_group_name = f'workspace_{self.workspace_id}'

        # Check if user is authenticated and a member
        if self.scope['user'].is_authenticated:
            is_member = await self.check_membership(self.workspace_id, self.scope['user'])
            if is_member:
                # Join room group
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.accept()
            else:
                await self.close()
        else:
            await self.close()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        username = self.scope['user'].username

        # Save message to database
        await self.save_message(self.workspace_id, self.scope['user'].id, message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        username = event['username']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
        }))

    @database_sync_to_async
    def check_membership(self, workspace_id, user):
        workspace = Workspace.objects.get(id=workspace_id)
        return WorkspaceMember.objects.filter(workspace=workspace, user=user).exists()

    @database_sync_to_async
    def save_message(self, workspace_id, user_id, message):
        workspace = Workspace.objects.get(id=workspace_id)
        user = User.objects.get(id=user_id)
        ChatMessage.objects.create(
            workspace=workspace,
            user=user,
            message=message
        )




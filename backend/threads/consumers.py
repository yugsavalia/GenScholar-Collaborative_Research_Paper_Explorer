import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Thread, Message
from workspaces.models import Workspace, WorkspaceMember


class ThreadConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.workspace_id = self.scope['url_route']['kwargs']['workspace_id']
        self.pdf_id = self.scope['url_route']['kwargs']['pdf_id']
        self.room_group_name = f'threads_workspace_{self.workspace_id}_pdf_{self.pdf_id}'
        
        if self.scope['user'].is_authenticated:
            is_member = await self.check_membership(self.workspace_id, self.scope['user'])
            if is_member:
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
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        pass
    
    async def thread_created(self, event):
        await self.send(text_data=json.dumps({
            'type': 'thread.created',
            'thread': event['thread']
        }))
    
    async def message_created(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message.created',
            'thread_id': event['thread_id'],
            'message': event['message']
        }))
    
    @database_sync_to_async
    def check_membership(self, workspace_id, user):
        try:
            workspace = Workspace.objects.get(id=workspace_id)
            return WorkspaceMember.objects.filter(workspace=workspace, user=user).exists()
        except Workspace.DoesNotExist:
            return False


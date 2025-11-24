import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Thread, Message
from workspaces.models import Workspace, WorkspaceMember


class ThreadConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time thread updates."""
    
    async def connect(self):
        """Connect to thread updates for a specific PDF."""
        self.workspace_id = self.scope['url_route']['kwargs']['workspace_id']
        self.pdf_id = self.scope['url_route']['kwargs']['pdf_id']
        self.room_group_name = f'threads_workspace_{self.workspace_id}_pdf_{self.pdf_id}'
        
        # Check authentication and membership
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
        """Leave room group on disconnect."""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receive message from WebSocket (not used for threads, messages go via HTTP API)."""
        # Threads use HTTP API for creating messages, WebSocket is only for broadcasting
        pass
    
    # Handler for thread.created event
    async def thread_created(self, event):
        """Broadcast when a new thread is created."""
        await self.send(text_data=json.dumps({
            'type': 'thread.created',
            'thread': event['thread']
        }))
    
    # Handler for message.created event
    async def message_created(self, event):
        """Broadcast when a new message is added to a thread."""
        await self.send(text_data=json.dumps({
            'type': 'message.created',
            'thread_id': event['thread_id'],
            'message': event['message']
        }))
    
    @database_sync_to_async
    def check_membership(self, workspace_id, user):
        """Check if user is a member of the workspace."""
        try:
            workspace = Workspace.objects.get(id=workspace_id)
            return WorkspaceMember.objects.filter(workspace=workspace, user=user).exists()
        except Workspace.DoesNotExist:
            return False


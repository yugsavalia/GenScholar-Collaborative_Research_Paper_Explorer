import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import ChatMessage
from workspaces.models import Workspace, WorkspaceMember


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.workspace_id = self.scope['url_route']['kwargs']['workspace_id']
        # --- This is the correct group name ---
        self.room_group_name = f'workspace_{self.workspace_id}'

        # Check if user is authenticated and a member
        if self.scope['user'].is_authenticated:
            is_member = await self.check_membership(self.workspace_id, self.scope['user'])
            # Also check role - REVIEWER can access Main Chat (this is allowed)
            # But we still check membership for security
            user_role = await self.get_user_role(self.workspace_id, self.scope['user'])
            if is_member and user_role:
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

    # Receive message from WebSocket (from a human user)
    async def receive(self, text_data):
        # Double-check role on message receive (defense in depth)
        user_role = await self.get_user_role(self.workspace_id, self.scope['user'])
        if not user_role:
            await self.close()
            return
        
        data = json.loads(text_data)
        message = data['message']
        username = self.scope['user'].username

        # Save message to database
        # --- We will get the timestamp from the saved object ---
        saved_message = await self.save_message(self.workspace_id, self.scope['user'].id, message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'id': saved_message.id,
                'message': saved_message.message,
                'username': username,
                'timestamp': saved_message.timestamp.isoformat()
            }
        )

    # Receive message from room group (from human OR AI Bot)
    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        timestamp = event.get('timestamp', '')
        message_id = event.get('id')

        # Send message down to the WebSocket (the frontend)
        await self.send(text_data=json.dumps({
            'id': message_id,
            'message': message,
            'username': username,
            'timestamp': timestamp
        }))

    @database_sync_to_async
    def check_membership(self, workspace_id, user):
        workspace = Workspace.objects.get(id=workspace_id)
        return WorkspaceMember.objects.filter(workspace=workspace, user=user).exists()

    @database_sync_to_async
    def save_message(self, workspace_id, user_id, message):
        workspace = Workspace.objects.get(id=workspace_id)
        user = User.objects.get(id=user_id)
        # --- UPDATED: Return the created message ---
        new_message = ChatMessage.objects.create(
            workspace=workspace,
            user=user,
            message=message
        )
        # Detect mentions and create notifications (sync call)
        self.create_mention_notifications_sync(new_message, workspace)
        return new_message # Return it so we can get its timestamp
    
    def create_mention_notifications_sync(self, message, workspace):
        """Detect @mentions in message and create notifications for mentioned users (sync version)."""
        import re
        from workspaces.models import Notification, WorkspaceMember
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        # Extract usernames after @
        mentions = re.findall(r'@([A-Za-z0-9_]+)', message.message)
        if not mentions:
            return
        
        # Get workspace members
        members = WorkspaceMember.objects.filter(workspace=workspace).select_related('user')
        
        # Create notification for each mentioned user
        for username in mentions:
            try:
                mentioned_member = members.get(user__username=username)
                mentioned_user = mentioned_member.user
                
                # Don't notify if user mentioned themselves
                if mentioned_user.id == message.user.id:
                    continue
                
                notification = Notification.objects.create(
                    user=mentioned_user,
                    type=Notification.NotificationType.MENTION,
                    title="You were mentioned",
                    message=f"{message.user.username} mentioned you in {workspace.name}: {message.message[:100]}",
                    related_workspace=workspace
                )
                
                channel_layer = get_channel_layer()
                unread_count = Notification.objects.filter(user=mentioned_user, is_read=False).count()
                async_to_sync(channel_layer.group_send)(
                    f"user_{mentioned_user.id}",
                    {
                        "type": "send_notification",
                        "data": {
                            "id": notification.id,
                            "message": notification.message,
                            "created_at": str(notification.created_at),
                            "unread_count": unread_count,
                        },
                    },
                )
            except WorkspaceMember.DoesNotExist:
                # User not in workspace, skip
                continue

    @database_sync_to_async
    def get_user_role(self, workspace_id, user):
        """Get user's role in the workspace. Returns role string or None if not a member."""
        try:
            workspace = Workspace.objects.get(id=workspace_id)
            member = WorkspaceMember.objects.get(workspace=workspace, user=user)
            return member.role
        except (Workspace.DoesNotExist, WorkspaceMember.DoesNotExist):
            return None
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, NotFound
from django.db.models import Prefetch
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from workspaces.models import Workspace, WorkspaceMember
from pdfs.models import PDFFile
from .models import Thread, Message
from .serializers import (
    ThreadSerializer,
    ThreadDetailSerializer,
    CreateThreadSerializer,
    MessageSerializer,
    CreateMessageSerializer
)


class ThreadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing threads on PDF text selections.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get threads filtered by workspace and PDF."""
        workspace_id = self.request.query_params.get('workspace_id')
        pdf_id = self.request.query_params.get('pdf_id')
        
        queryset = Thread.objects.select_related(
            'workspace', 'pdf', 'created_by'
        ).prefetch_related(
            Prefetch('messages', queryset=Message.objects.select_related('sender').order_by('created_at'))
        )
        
        if workspace_id:
            queryset = queryset.filter(workspace_id=workspace_id)
        if pdf_id:
            queryset = queryset.filter(pdf_id=pdf_id)
        
        return queryset.order_by('-last_activity_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return ThreadDetailSerializer
        elif self.action == 'create':
            return CreateThreadSerializer
        return ThreadSerializer
    
    def check_workspace_membership(self, workspace_id):
        """Check if user is a member of the workspace."""
        if not WorkspaceMember.objects.filter(
            workspace_id=workspace_id,
            user=self.request.user
        ).exists():
            raise PermissionDenied("You must be a member of this workspace to access threads.")
    
    def check_researcher_role(self, workspace_id):
        """Check if user is a researcher (not reviewer) in the workspace."""
        try:
            member = WorkspaceMember.objects.get(
                workspace_id=workspace_id,
                user=self.request.user
            )
            if member.role != WorkspaceMember.Role.RESEARCHER:
                raise PermissionDenied("Only researchers can perform this action.")
        except WorkspaceMember.DoesNotExist:
            raise PermissionDenied("You must be a member of this workspace to access threads.")
    
    def list(self, request, *args, **kwargs):
        """List threads for a workspace and PDF."""
        workspace_id = request.query_params.get('workspace_id')
        pdf_id = request.query_params.get('pdf_id')
        
        if not workspace_id or not pdf_id:
            return Response(
                {"error": "workspace_id and pdf_id query parameters are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check workspace membership
        self.check_workspace_membership(workspace_id)
        
        # Verify PDF belongs to workspace
        try:
            pdf = PDFFile.objects.get(id=pdf_id, workspace_id=workspace_id)
        except PDFFile.DoesNotExist:
            raise NotFound("PDF not found in this workspace")
        
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create a new thread from a text selection."""
        workspace_id = request.data.get('workspace_id') or request.query_params.get('workspace_id')
        pdf_id = request.data.get('pdf_id')
        
        if not workspace_id or not pdf_id:
            return Response(
                {"error": "workspace_id and pdf_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check workspace membership and researcher role
        self.check_researcher_role(workspace_id)
        
        # Verify PDF belongs to workspace
        try:
            pdf = PDFFile.objects.get(id=pdf_id, workspace_id=workspace_id)
        except PDFFile.DoesNotExist:
            raise NotFound("PDF not found in this workspace")
        
        # Create thread - convert pdf_id to pdf for serializer
        serializer_data = {k: v for k, v in request.data.items() if k not in ['workspace_id', 'pdf_id']}
        serializer_data['pdf'] = pdf.id  # Use the pdf object we already fetched
        serializer = CreateThreadSerializer(data=serializer_data)
        serializer.is_valid(raise_exception=True)
        
        thread = serializer.save(
            workspace_id=workspace_id,
            pdf=pdf,
            created_by=request.user
        )
        
        # Return minimal thread data immediately (don't wait for WebSocket)
        # WebSocket broadcast happens asynchronously
        thread_serializer = ThreadSerializer(thread)
        
        # Broadcast thread creation via WebSocket (async, non-blocking)
        try:
            self.broadcast_thread_created(thread)
        except Exception as e:
            # Don't fail the request if broadcast fails
            print(f"Warning: Failed to broadcast thread creation: {e}")
        
        return Response(thread_serializer.data, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        """Get a thread with all its messages."""
        thread = self.get_object()
        
        # Check workspace membership
        self.check_workspace_membership(thread.workspace_id)
        
        serializer = ThreadDetailSerializer(thread)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def messages(self, request, pk=None):
        """Add a message to a thread."""
        thread = self.get_object()
        
        # Check workspace membership and researcher role
        self.check_researcher_role(thread.workspace_id)
        
        serializer = CreateMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = serializer.save(
            thread=thread,
            sender=request.user
        )
        
        # Update thread's last_activity_at
        thread.last_activity_at = timezone.now()
        thread.save(update_fields=['last_activity_at'])
        
        # Detect mentions and create notifications
        self.create_mention_notifications(message, thread.workspace)
        
        # Return minimal message data immediately
        message_serializer = MessageSerializer(message)
        
        # Broadcast message creation via WebSocket (async, non-blocking)
        try:
            self.broadcast_message_created(thread, message)
        except Exception as e:
            # Don't fail the request if broadcast fails
            print(f"Warning: Failed to broadcast message creation: {e}")
        
        return Response(message_serializer.data, status=status.HTTP_201_CREATED)
    
    def create_mention_notifications(self, message, workspace):
        """Detect @mentions in message and create notifications for mentioned users."""
        import re
        from workspaces.models import Notification, WorkspaceMember
        
        # Extract usernames after @
        mentions = re.findall(r'@([A-Za-z0-9_]+)', message.content)
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
                if mentioned_user.id == message.sender.id:
                    continue
                
                from workspaces.models import Notification
                notification = Notification.objects.create(
                    user=mentioned_user,
                    type=Notification.NotificationType.MENTION,
                    title="You were mentioned",
                    message=f"{message.sender.username} mentioned you in {workspace.name}: {message.content[:100]}",
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
    
    @action(detail=True, methods=['get'])
    def get_messages(self, request, pk=None):
        """Get all messages for a thread (paginated)."""
        thread = self.get_object()
        
        # Check workspace membership
        self.check_workspace_membership(thread.workspace_id)
        
        messages = thread.messages.select_related('sender').order_by('created_at')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    def broadcast_thread_created(self, thread):
        """Broadcast thread creation via WebSocket with minimal payload."""
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                group_name = f'threads_workspace_{thread.workspace_id}_pdf_{thread.pdf_id}'
                # Send minimal thread data (avoid heavy serialization)
                thread_data = {
                    'id': thread.id,
                    'page_number': thread.page_number,
                    'selection_text': thread.selection_text[:100],  # Truncate for preview
                    'anchor_rect': thread.anchor_rect,
                    'anchor_side': thread.anchor_side,
                    'created_by': {'id': thread.created_by.id, 'username': thread.created_by.username} if thread.created_by else None,
                    'created_at': thread.created_at.isoformat(),
                    'last_activity_at': thread.last_activity_at.isoformat(),
                    'message_count': 0,
                }
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'thread_created',
                        'thread': thread_data
                    }
                )
        except (ConnectionRefusedError, OSError) as e:
            # Redis connection refused - log once and continue
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Redis not available, WS broadcasting disabled — using in-memory fallback. Error: {e}")
        except Exception as e:
            # Don't fail the request if WebSocket broadcast fails
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error broadcasting thread creation: {e}")
    
    def broadcast_message_created(self, thread, message):
        """Broadcast message creation via WebSocket with minimal payload."""
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                group_name = f'threads_workspace_{thread.workspace_id}_pdf_{thread.pdf_id}'
                # Send minimal message data (avoid heavy serialization)
                message_data = {
                    'id': message.id,
                    'content': message.content,
                    'sender': {'id': message.sender.id, 'username': message.sender.username} if message.sender else None,
                    'created_at': message.created_at.isoformat(),
                    'edited_at': message.edited_at.isoformat() if message.edited_at else None,
                }
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'message_created',
                        'thread_id': thread.id,
                        'message': message_data
                    }
                )
        except (ConnectionRefusedError, OSError) as e:
            # Redis connection refused - log once and continue
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Redis not available, WS broadcasting disabled — using in-memory fallback. Error: {e}")
        except Exception as e:
            # Don't fail the request if WebSocket broadcast fails
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error broadcasting message creation: {e}")


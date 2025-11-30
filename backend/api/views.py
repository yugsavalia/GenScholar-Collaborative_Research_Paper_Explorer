import json
from django.contrib.auth.models import User
from django.db.models import Prefetch
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, NotFound

from chat.models import ChatMessage
from pdfs.models import PDFFile, Annotation
from workspaces.models import Workspace, WorkspaceMember, WorkspaceInvitation, Notification, PinnedNote

from .serializers import (
    AnnotationSerializer,
    MessageSerializer,
    PDFSerializer,
    UserSerializer,
    WorkspaceMemberSerializer,
    WorkspaceSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.query_params.get('q', '')
        if search_query:
            queryset = queryset.filter(username__icontains=search_query) | queryset.filter(email__icontains=search_query)
        return queryset


class WorkspaceViewSet(viewsets.ModelViewSet):
    queryset = Workspace.objects.all().prefetch_related(
        Prefetch(
            'members',
            queryset=WorkspaceMember.objects.select_related('user'),
        ),
        'created_by',
    )
    serializer_class = WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied('Authentication required.')

        workspace = serializer.save(created_by=self.request.user)
        WorkspaceMember.objects.get_or_create(workspace=workspace, user=self.request.user)


class PDFViewSet(viewsets.ModelViewSet):
    queryset = PDFFile.objects.all().select_related('workspace', 'uploaded_by')
    serializer_class = PDFSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """Filter PDFs by workspace if provided, and ensure user has access."""
        queryset = super().get_queryset()
        
        # Filter by workspace if provided
        workspace_id = self.request.query_params.get('workspace')
        print(f"[PDFViewSet] get_queryset called - workspace_id: {workspace_id}, user: {self.request.user.id if self.request.user.is_authenticated else 'anonymous'}")
        if workspace_id:
            try:
                workspace_id = int(workspace_id)
                queryset = queryset.filter(workspace_id=workspace_id)
                
                # Ensure user is a member of the workspace (if authenticated)
                # Note: For read operations, we allow if user is authenticated
                # The permission check ensures they can only see PDFs from their workspaces
                if self.request.user.is_authenticated:
                    from workspaces.models import WorkspaceMember, Workspace
                    # Check if user is a member OR is the creator
                    try:
                        workspace = Workspace.objects.get(id=workspace_id)
                        is_member = WorkspaceMember.objects.filter(workspace_id=workspace_id, user=self.request.user).exists()
                        is_creator = workspace.created_by == self.request.user
                        
                        if not is_member and not is_creator:
                            # User is not a member or creator - return empty queryset
                            print(f"[PDFViewSet] User {self.request.user.id} is not a member or creator of workspace {workspace_id}")
                            return queryset.none()
                        else:
                            pdf_count = queryset.count()
                            print(f"[PDFViewSet] User {self.request.user.id} is {'member' if is_member else 'creator'} of workspace {workspace_id}, found {pdf_count} PDFs")
                    except Workspace.DoesNotExist:
                        print(f"[PDFViewSet] Workspace {workspace_id} does not exist")
                        return queryset.none()
                else:
                    # Unauthenticated users get empty queryset
                    print(f"[PDFViewSet] User is not authenticated")
                    return queryset.none()
            except (ValueError, TypeError) as e:
                # Invalid workspace_id, return empty queryset
                print(f"[PDFViewSet] Invalid workspace_id: {workspace_id}, error: {e}")
                return queryset.none()
        else:
            # No workspace filter - only return PDFs from workspaces user is a member of
            if self.request.user.is_authenticated:
                from workspaces.models import WorkspaceMember
                user_workspaces = WorkspaceMember.objects.filter(user=self.request.user).values_list('workspace_id', flat=True)
                queryset = queryset.filter(workspace_id__in=user_workspaces)
            else:
                queryset = queryset.none()
        
        final_count = queryset.count()
        print(f"[PDFViewSet] Final queryset count: {final_count}")
        return queryset

    def create(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        if file:
            workspace_id = request.data.get('workspace')
            if workspace_id:
                filename = file.name
                if PDFFile.objects.filter(workspace_id=workspace_id, title__iexact=filename).exists():
                    from rest_framework.response import Response
                    from rest_framework import status
                    return Response({"error": "A PDF with this name already exists in this workspace."}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied('Authentication required.')
        # Handle file upload - read bytes from uploaded file
        file = self.request.FILES.get('file')
        if file:
            pdf_bytes = file.read()
            serializer.save(uploaded_by=self.request.user, file=pdf_bytes)
        else:
            raise PermissionDenied('PDF file is required.')
    
    def perform_destroy(self, instance):
        """Delete PDF and handle workspace index cleanup."""
        import os
        import shutil
        
        workspace = instance.workspace
        
        # Check if user is a researcher in the workspace
        member = WorkspaceMember.objects.filter(workspace=workspace, user=self.request.user).first()
        if not member or member.role != WorkspaceMember.Role.RESEARCHER:
            raise PermissionDenied('Only researchers can delete PDFs.')
        
        # Delete the entire workspace index if it exists
        if workspace.index_path and os.path.exists(workspace.index_path):
            try:
                shutil.rmtree(workspace.index_path)
            except Exception as e:
                print(f"Error deleting workspace index: {e}")
        
        # Delete the PDF (annotations will be deleted automatically via CASCADE)
        instance.delete()
        
        # Reset all remaining PDFs to be re-indexed
        remaining_pdfs = workspace.pdf_files.all()
        if remaining_pdfs.exists():
            remaining_pdfs.update(is_indexed=False)
            workspace.processing_status = Workspace.ProcessingStatus.PROCESSING
        else:
            workspace.processing_status = Workspace.ProcessingStatus.NONE
        
        workspace.index_path = None
        workspace.save()
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download PDF file as bytes - separate endpoint for binary data."""
        # Get PDF directly by ID, bypassing queryset filtering
        # We'll check permissions manually
        try:
            pdf = PDFFile.objects.get(id=pk)
        except PDFFile.DoesNotExist:
            raise NotFound('PDF not found.')
        
        # Check workspace membership
        from workspaces.models import WorkspaceMember
        if not request.user.is_authenticated:
            raise PermissionDenied('Authentication required.')
        
        if not WorkspaceMember.objects.filter(workspace=pdf.workspace, user=request.user).exists():
            raise PermissionDenied('You do not have permission to access this PDF.')
        
        response = HttpResponse(pdf.file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{pdf.title}.pdf"'
        return response
    
    @action(detail=True, methods=['get'], url_path='file')
    def file(self, request, pk=None):
        """Alias for download endpoint - /api/pdfs/<id>/file/"""
        return self.download(request, pk)


class AnnotationViewSet(viewsets.ModelViewSet):
    queryset = Annotation.objects.all().select_related('pdf', 'created_by')
    serializer_class = AnnotationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        pdf_id = self.request.query_params.get('pdf_id')
        if pdf_id:
            queryset = queryset.filter(pdf_id=pdf_id)
        return queryset

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied('Authentication required.')
        serializer.save(created_by=self.request.user)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = ChatMessage.objects.all().select_related('workspace', 'user')
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        workspace_id = self.request.query_params.get('workspace_id')
        if workspace_id:
            queryset = queryset.filter(workspace_id=workspace_id)
        return queryset

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied('Authentication required.')
        message = serializer.save(user=self.request.user)
        # Detect mentions and create notifications
        self.create_mention_notifications(message)
    
    def create_mention_notifications(self, message):
        """Detect @mentions in message and create notifications for mentioned users."""
        import re
        from workspaces.models import Notification, WorkspaceMember
        
        # Extract usernames after @
        mentions = re.findall(r'@([A-Za-z0-9_]+)', message.message)
        if not mentions:
            return
        
        # Get workspace members
        workspace = message.workspace
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
                
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
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


# Function-based API views for workspace member management

@require_http_methods(["GET"])
def api_workspace_members_view(request, workspace_id):
    """
    GET /api/workspaces/:workspaceId/members/
    List all members of a workspace with their roles.
    Permission: Must be a member of the workspace.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Authentication required"}, status=401)
    
    try:
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return JsonResponse({"success": False, "message": "Workspace not found"}, status=404)
        
        # Check if user is a member of the workspace
        is_member = WorkspaceMember.objects.filter(workspace=workspace, user=request.user).exists()
        print(f"[api_workspace_members_view] User {request.user.id} checking workspace {workspace_id}: is_member={is_member}")
        if not is_member:
            # Also check if user is the creator (they should have access even if not explicitly a member)
            if workspace.created_by == request.user:
                print(f"[api_workspace_members_view] User {request.user.id} is creator of workspace {workspace_id}, allowing access")
            else:
                return JsonResponse({"success": False, "message": "You do not have permission to access this workspace"}, status=403)
        
        # Get all members
        members = WorkspaceMember.objects.filter(workspace=workspace).select_related('user')
        
        # Serialize members
        members_data = []
        for member in members:
            is_creator = member.user.id == workspace.created_by.id
            members_data.append({
                "id": member.id,
                "user": {
                    "id": member.user.id,
                    "username": member.user.username,
                    "email": member.user.email
                },
                "role": member.role,
                "is_creator": is_creator,
                "joined_at": member.joined_at.isoformat()
            })
        
        return JsonResponse({
            "success": True,
            "data": {"members": members_data}
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@require_http_methods(["GET"])
def api_workspace_mentionable_users_view(request, workspace_id):
    """
    GET /api/workspaces/:workspaceId/mentionable-users/
    List all workspace members for @mention autocomplete.
    Permission: Must be a member of the workspace.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Authentication required"}, status=401)
    
    try:
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return JsonResponse({"success": False, "message": "Workspace not found"}, status=404)
        
        # Check if user is a member of the workspace
        is_member = WorkspaceMember.objects.filter(workspace=workspace, user=request.user).exists()
        if not is_member and workspace.created_by != request.user:
            return JsonResponse({"success": False, "message": "You do not have permission to access this workspace"}, status=403)
        
        # Get all members
        members = WorkspaceMember.objects.filter(workspace=workspace).select_related('user')
        
        # Serialize members for mention autocomplete
        users_data = []
        for member in members:
            users_data.append({
                "id": member.user.id,
                "username": member.user.username,
                "email": member.user.email
            })
        
        return JsonResponse({
            "success": True,
            "data": {"users": users_data}
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


def user_is_researcher_in_workspace(user, workspace):
    """Check if user is a researcher or creator in the workspace."""
    if workspace.created_by == user:
        return True
    try:
        member = WorkspaceMember.objects.get(workspace=workspace, user=user)
        return member.role == WorkspaceMember.Role.RESEARCHER
    except WorkspaceMember.DoesNotExist:
        return False


@require_http_methods(["GET", "POST", "PUT", "DELETE"])
def api_workspace_pinned_note_view(request, workspace_id):
    """
    GET/POST/PUT/DELETE /api/workspaces/:workspaceId/pinned-note/
    Manage pinned notes for a workspace.
    GET: Anyone with workspace access can view
    POST/PUT/DELETE: Only researchers or workspace creator can modify
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Authentication required"}, status=401)
    
    try:
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return JsonResponse({"success": False, "message": "Workspace not found"}, status=404)
        
        # Check if user is a member of the workspace
        is_member = WorkspaceMember.objects.filter(workspace=workspace, user=request.user).exists()
        if not is_member and workspace.created_by != request.user:
            return JsonResponse({"success": False, "message": "You do not have permission to access this workspace"}, status=403)
        
        if request.method == "GET":
            # Anyone with access can view
            note = getattr(workspace, 'pinned_note', None)
            if not note:
                return JsonResponse({
                    "success": True,
                    "data": {
                        "content": "",
                        "author": None,
                        "updated_at": None
                    }
                })
            return JsonResponse({
                "success": True,
                "data": {
                    "content": note.content,
                    "author": {
                        "id": note.author.id,
                        "username": note.author.username
                    } if note.author else None,
                    "updated_at": note.updated_at.isoformat()
                }
            })
        
        else:
            # POST/PUT/DELETE require researcher or creator
            if not user_is_researcher_in_workspace(request.user, workspace):
                return JsonResponse({"success": False, "message": "Only researchers may modify pinned notes"}, status=403)
            
            if request.method in ("POST", "PUT"):
                data = json.loads(request.body)
                content = data.get("content", "").strip()
                
                # Limit content length
                if len(content) > 10000:
                    return JsonResponse({"success": False, "message": "Content too long (max 10000 characters)"}, status=400)
                
                note, created = PinnedNote.objects.get_or_create(
                    workspace=workspace,
                    defaults={"author": request.user, "content": content}
                )
                
                if not created:
                    note.content = content
                    note.author = request.user
                    note.save()
                
                return JsonResponse({
                    "success": True,
                    "data": {
                        "content": note.content,
                        "author": {
                            "id": note.author.id,
                            "username": note.author.username
                        } if note.author else None,
                        "updated_at": note.updated_at.isoformat()
                    }
                })
            
            elif request.method == "DELETE":
                note = getattr(workspace, 'pinned_note', None)
                if note:
                    note.delete()
                return JsonResponse({"success": True}, status=204)
    
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@require_http_methods(["POST"])
def api_workspace_invite_view(request, workspace_id):
    """
    POST /api/workspaces/:workspaceId/invite/
    Invite an existing user to the workspace by username.
    Request: { "username": "<target_username>" }
    Permission: Only users with RESEARCHER role can invite.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)
    
    try:
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return JsonResponse({"error": "Workspace not found"}, status=404)
        
        # Check if user is a member and has RESEARCHER role (or is creator)
        is_creator = workspace.created_by == request.user
        is_member = WorkspaceMember.objects.filter(workspace=workspace, user=request.user).exists()
        
        if not is_creator and not is_member:
            return JsonResponse({"error": "You are not a member of this workspace"}, status=403)
        
        if not is_creator:
            try:
                user_membership = WorkspaceMember.objects.get(workspace=workspace, user=request.user)
                if user_membership.role != WorkspaceMember.Role.RESEARCHER:
                    return JsonResponse({"error": "Only researchers can invite users"}, status=403)
            except WorkspaceMember.DoesNotExist:
                return JsonResponse({"error": "You are not a member of this workspace"}, status=403)
        
        # Parse request data
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        role_str = data.get('role', 'RESEARCHER').upper()
        
        if not username:
            return JsonResponse({"error": "Username is required"}, status=400)
        
        # Validate role
        valid_roles = [WorkspaceMember.Role.RESEARCHER, WorkspaceMember.Role.REVIEWER]
        if role_str not in valid_roles:
            role_str = WorkspaceMember.Role.RESEARCHER  # Default to RESEARCHER if invalid
        
        # Get the user to invite by username (case-insensitive)
        try:
            user_to_invite = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            return JsonResponse({"error": "User does not exist."}, status=400)
        
        # Check if already a member
        if WorkspaceMember.objects.filter(workspace=workspace, user=user_to_invite).exists():
            return JsonResponse({"error": "User is already a member of this workspace."}, status=400)
        
        # Check if there's already a pending invitation
        existing_invitation = WorkspaceInvitation.objects.filter(
            workspace=workspace,
            invited_user=user_to_invite,
            status=WorkspaceInvitation.Status.PENDING
        ).first()
        
        if existing_invitation:
            return JsonResponse({"error": "User already has a pending invite."}, status=400)
        
        # Create invitation with specified role (default to RESEARCHER)
        invitation = WorkspaceInvitation.objects.create(
            workspace=workspace,
            invited_by=request.user,
            invited_user=user_to_invite,
            role=role_str,
            status=WorkspaceInvitation.Status.PENDING
        )
        
        # Create notification for the invited user with role information
        role_display = "Researcher" if role_str == WorkspaceMember.Role.RESEARCHER else "Reviewer"
        notification = Notification.objects.create(
            user=user_to_invite,
            type=Notification.NotificationType.INVITATION,
            title="Workspace Invitation",
            message=f"{request.user.username} has invited you to join workspace {workspace.name}. You were invited as {role_display}.",
            related_workspace=workspace,
            related_invitation=invitation
        )
        
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        unread_count = Notification.objects.filter(user=user_to_invite, is_read=False).count()
        async_to_sync(channel_layer.group_send)(
            f"user_{user_to_invite.id}",
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
        
        return JsonResponse({"success": True})
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["PATCH"])
def api_workspace_member_role_view(request, workspace_id, member_id):
    """
    PATCH /api/workspaces/:workspaceId/members/:memberId/
    Update the role of a workspace member.
    Request: { role }
    Permission: Only workspace creator can change roles.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Authentication required"}, status=401)
    
    try:
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return JsonResponse({"success": False, "message": "Workspace not found"}, status=404)
        
        # Check if user is the workspace creator
        if workspace.created_by != request.user:
            return JsonResponse({"success": False, "message": "Only the workspace creator can change member roles"}, status=403)
        
        # Verify user is a member of the workspace
        if not WorkspaceMember.objects.filter(workspace=workspace, user=request.user).exists():
            return JsonResponse({"success": False, "message": "You are not a member of this workspace"}, status=403)
        
        # Get the member to update
        try:
            member = WorkspaceMember.objects.get(id=member_id, workspace=workspace)
        except WorkspaceMember.DoesNotExist:
            return JsonResponse({"success": False, "message": "Member not found"}, status=404)
        
        # Parse request data
        data = json.loads(request.body)
        new_role = data.get('role')
        
        if not new_role:
            return JsonResponse({"success": False, "message": "role is required"}, status=400)
        
        # Validate role
        valid_roles = [WorkspaceMember.Role.RESEARCHER, WorkspaceMember.Role.REVIEWER]
        if new_role not in valid_roles:
            return JsonResponse({"success": False, "message": f"Invalid role. Must be one of: {', '.join(valid_roles)}"}, status=400)
        
        # Prevent creator from changing their own role (optional safety check)
        if member.user == request.user:
            return JsonResponse({"success": False, "message": "You cannot change your own role"}, status=400)
        
        # Update the role
        member.role = new_role
        member.save()
        
        # Serialize and return
        is_creator = member.user.id == workspace.created_by.id
        member_data = {
            "id": member.id,
            "user": {
                "id": member.user.id,
                "username": member.user.username,
                "email": member.user.email
            },
            "role": member.role,
            "is_creator": is_creator,
            "joined_at": member.joined_at.isoformat()
        }
        
        return JsonResponse({
            "success": True,
            "data": {"member": member_data}
        })
        
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@require_http_methods(["GET"])
def api_invitations_view(request):
    """
    GET /api/invitations/
    List all pending invitations for the current user.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Authentication required"}, status=401)
    
    try:
        invitations = WorkspaceInvitation.objects.filter(
            invited_user=request.user,
            status=WorkspaceInvitation.Status.PENDING
        ).select_related('workspace', 'invited_by').order_by('-created_at')
        
        invitations_data = []
        for invitation in invitations:
            invitations_data.append({
                "id": invitation.id,
                "workspace": {
                    "id": invitation.workspace.id,
                    "name": invitation.workspace.name
                },
                "invited_by": {
                    "id": invitation.invited_by.id,
                    "username": invitation.invited_by.username,
                    "email": invitation.invited_by.email
                },
                "role": invitation.role,
                "status": invitation.status,
                "created_at": invitation.created_at.isoformat()
            })
        
        return JsonResponse({
            "success": True,
            "data": {"invitations": invitations_data}
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@require_http_methods(["POST"])
def api_accept_invitation_view(request, invitation_id):
    """
    POST /api/invitations/:invitationId/accept/
    Accept a workspace invitation and create membership.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Authentication required"}, status=401)
    
    try:
        try:
            invitation = WorkspaceInvitation.objects.get(
                id=invitation_id,
                invited_user=request.user,
                status=WorkspaceInvitation.Status.PENDING
            )
        except WorkspaceInvitation.DoesNotExist:
            return JsonResponse({"success": False, "message": "Invitation not found or already processed"}, status=404)
        
        # Check if user is already a member - if so, update their role to the invited role
        existing_member = WorkspaceMember.objects.filter(
            workspace=invitation.workspace, 
            user=request.user
        ).first()
        
        if existing_member:
            # Update existing member's role to the invited role
            existing_member.role = invitation.role
            existing_member.save()
            member = existing_member
        else:
            # Create new membership with the role specified in the invitation
            member = WorkspaceMember.objects.create(
                workspace=invitation.workspace,
                user=request.user,
                role=invitation.role
            )
        
        # Update invitation status and set responded_at
        from django.utils import timezone
        invitation.status = WorkspaceInvitation.Status.ACCEPTED
        invitation.responded_at = timezone.now()
        invitation.save()
        
        # Mark related notification as read
        Notification.objects.filter(
            user=request.user,
            related_invitation=invitation
        ).update(is_read=True)
        
        # Serialize and return
        is_creator = member.user.id == invitation.workspace.created_by.id
        member_data = {
            "id": member.id,
            "user": {
                "id": member.user.id,
                "username": member.user.username,
                "email": member.user.email
            },
            "role": member.role,
            "is_creator": is_creator,
            "joined_at": member.joined_at.isoformat()
        }
        
        return JsonResponse({
            "success": True,
            "data": {"member": member_data}
        })
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@require_http_methods(["POST"])
def api_decline_invitation_view(request, invitation_id):
    """
    POST /api/invitations/:invitationId/decline/
    Decline a workspace invitation.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Authentication required"}, status=401)
    
    try:
        try:
            invitation = WorkspaceInvitation.objects.get(
                id=invitation_id,
                invited_user=request.user,
                status=WorkspaceInvitation.Status.PENDING
            )
        except WorkspaceInvitation.DoesNotExist:
            return JsonResponse({"success": False, "message": "Invitation not found or already processed"}, status=404)
        
        # Update invitation status and set responded_at
        from django.utils import timezone
        invitation.status = WorkspaceInvitation.Status.DECLINED
        invitation.responded_at = timezone.now()
        invitation.save()
        
        # Mark related notification as read
        Notification.objects.filter(
            user=request.user,
            related_invitation=invitation
        ).update(is_read=True)
        
        return JsonResponse({
            "success": True,
            "data": {"message": "Invitation declined"}
        })
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@require_http_methods(["GET"])
def api_notifications_view(request):
    """
    GET /api/notifications/
    List all notifications for the current user.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Authentication required"}, status=401)
    
    try:
        notifications = Notification.objects.filter(
            user=request.user
        ).select_related('related_workspace', 'related_invitation').order_by('-created_at')[:50]
        
        notifications_data = []
        for notification in notifications:
            # Get invitation role if this is an invitation notification
            invitation_role = None
            if notification.related_invitation:
                invitation_role = notification.related_invitation.role
                role_display = "Researcher" if invitation_role == WorkspaceMember.Role.RESEARCHER else "Reviewer"
            else:
                role_display = None
            
            notifications_data.append({
                "id": notification.id,
                "type": notification.type,
                "title": notification.title,
                "message": notification.message,
                "is_read": notification.is_read,
                "workspace": {
                    "id": notification.related_workspace.id,
                    "name": notification.related_workspace.name
                } if notification.related_workspace else None,
                "invitation_id": notification.related_invitation.id if notification.related_invitation else None,
                "workspace_id": notification.related_workspace.id if notification.related_workspace else None,
                "invitation_role": invitation_role,
                "invitation_role_display": role_display,
                "created_at": notification.created_at.isoformat()
            })
        
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        
        return JsonResponse({
            "success": True,
            "data": {
                "notifications": notifications_data,
                "unread_count": unread_count
            }
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@require_http_methods(["PATCH"])
def api_mark_notification_read_view(request, notification_id):
    """
    PATCH /api/notifications/:notificationId/
    Mark a notification as read.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Authentication required"}, status=401)
    
    try:
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
        except Notification.DoesNotExist:
            return JsonResponse({"success": False, "message": "Notification not found"}, status=404)
        
        notification.is_read = True
        notification.save()
        
        return JsonResponse({
            "success": True,
            "data": {"message": "Notification marked as read"}
        })
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


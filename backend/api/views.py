import json
from django.contrib.auth.models import User
from django.db.models import Prefetch
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from chat.models import ChatMessage
from pdfs.models import PDFFile, Annotation
from workspaces.models import Workspace, WorkspaceMember, WorkspaceInvitation, Notification

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
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied('Authentication required.')

        workspace = serializer.save(created_by=self.request.user)
        WorkspaceMember.objects.get_or_create(workspace=workspace, user=self.request.user)


class PDFViewSet(viewsets.ModelViewSet):
    queryset = PDFFile.objects.all().select_related('workspace', 'uploaded_by')
    serializer_class = PDFSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied('Authentication required.')
        serializer.save(uploaded_by=self.request.user)


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
        serializer.save(user=self.request.user)


# Function-based API views for workspace member management

@csrf_exempt
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
        if not WorkspaceMember.objects.filter(workspace=workspace, user=request.user).exists():
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


@csrf_exempt
@require_http_methods(["POST"])
def api_workspace_invite_view(request, workspace_id):
    """
    POST /api/workspaces/:workspaceId/invite/
    Invite an existing user to the workspace with a specific role.
    Request: { user_id, role }
    Permission: Only users with RESEARCHER role can invite.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Authentication required"}, status=401)
    
    try:
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return JsonResponse({"success": False, "message": "Workspace not found"}, status=404)
        
        # Check if user is a member and has RESEARCHER role
        try:
            user_membership = WorkspaceMember.objects.get(workspace=workspace, user=request.user)
            if user_membership.role != WorkspaceMember.Role.RESEARCHER:
                return JsonResponse({"success": False, "message": "Only researchers can invite users"}, status=403)
        except WorkspaceMember.DoesNotExist:
            return JsonResponse({"success": False, "message": "You are not a member of this workspace"}, status=403)
        
        # Parse request data
        data = json.loads(request.body)
        user_id = data.get('user_id')
        role_str = data.get('role', WorkspaceMember.Role.REVIEWER)
        
        if not user_id:
            return JsonResponse({"success": False, "message": "user_id is required"}, status=400)
        
        # Validate role
        valid_roles = [WorkspaceMember.Role.RESEARCHER, WorkspaceMember.Role.REVIEWER]
        if role_str not in valid_roles:
            return JsonResponse({"success": False, "message": f"Invalid role. Must be one of: {', '.join(valid_roles)}"}, status=400)
        
        # Get the user to invite
        try:
            user_to_invite = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({"success": False, "message": "User not found"}, status=404)
        
        # Check if already a member
        if WorkspaceMember.objects.filter(workspace=workspace, user=user_to_invite).exists():
            return JsonResponse({"success": False, "message": "User is already a member of this workspace"}, status=400)
        
        # Check if there's already a pending invitation
        existing_invitation = WorkspaceInvitation.objects.filter(
            workspace=workspace,
            invited_user=user_to_invite,
            status=WorkspaceInvitation.Status.PENDING
        ).first()
        
        if existing_invitation:
            return JsonResponse({"success": False, "message": "User already has a pending invitation"}, status=400)
        
        # Create invitation instead of direct membership
        invitation = WorkspaceInvitation.objects.create(
            workspace=workspace,
            invited_by=request.user,
            invited_user=user_to_invite,
            role=role_str,
            status=WorkspaceInvitation.Status.PENDING
        )
        
        # Create notification for the invited user
        Notification.objects.create(
            user=user_to_invite,
            type=Notification.NotificationType.INVITATION,
            title=f"Invitation to {workspace.name}",
            message=f"{request.user.username} invited you to join '{workspace.name}' as a {role_str}",
            related_workspace=workspace,
            related_invitation=invitation
        )
        
        # Serialize and return invitation
        invitation_data = {
            "id": invitation.id,
            "workspace": {
                "id": workspace.id,
                "name": workspace.name
            },
            "invited_by": {
                "id": request.user.id,
                "username": request.user.username,
                "email": request.user.email
            },
            "invited_user": {
                "id": user_to_invite.id,
                "username": user_to_invite.username,
                "email": user_to_invite.email
            },
            "role": invitation.role,
            "status": invitation.status,
            "created_at": invitation.created_at.isoformat()
        }
        
        return JsonResponse({
            "success": True,
            "data": {"invitation": invitation_data}
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
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


@csrf_exempt
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


@csrf_exempt
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
        
        # Check if user is already a member
        if WorkspaceMember.objects.filter(workspace=invitation.workspace, user=request.user).exists():
            invitation.status = WorkspaceInvitation.Status.DECLINED
            invitation.save()
            return JsonResponse({"success": False, "message": "You are already a member of this workspace"}, status=400)
        
        # Create membership
        member = WorkspaceMember.objects.create(
            workspace=invitation.workspace,
            user=request.user,
            role=invitation.role
        )
        
        # Update invitation status
        invitation.status = WorkspaceInvitation.Status.ACCEPTED
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


@csrf_exempt
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
        
        # Update invitation status
        invitation.status = WorkspaceInvitation.Status.DECLINED
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


@csrf_exempt
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


@csrf_exempt
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


import os
import shutil
import json
from django.conf import settings
from django.views.decorators.http import require_POST, require_http_methods
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from .models import Workspace, WorkspaceMember, Notification
from pdfs.models import PDFFile
from chatbot.models import AIChatMessage

@login_required
def dashboard_view(request):
    # --- UPDATED: Search Logic ---
    search_query = request.GET.get('q', '') # Get the search query, or default to empty
    
    # Get base workspaces
    workspaces = Workspace.objects.filter(members__user=request.user).distinct()
    
    if search_query:
        # Filter by name if a query exists
        workspaces = workspaces.filter(name__icontains=search_query)

    return render(request, 'workspaces/dashboard.html', {
        'workspaces': workspaces,
        'search_query': search_query # Pass the query back to the template
    })


@login_required
def create_workspace_view(request):
    if request.method == 'POST':
        name = request.POST['name']
        workspace = Workspace.objects.create(name=name, created_by=request.user)
        # Add creator as member with researcher role
        WorkspaceMember.objects.create(
            workspace=workspace, 
            user=request.user,
            role=WorkspaceMember.Role.RESEARCHER
        )
        return redirect('workspace_detail', workspace_id=workspace.id)
    
    return redirect('dashboard')


@login_required
def workspace_detail_view(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)
    
    # Check if user is a member and get their membership (including role)
    try:
        user_membership = WorkspaceMember.objects.get(workspace=workspace, user=request.user)
        current_user_role = user_membership.role
    except WorkspaceMember.DoesNotExist:
        return redirect('dashboard')
    
    # --- UPDATED: PDF Search Logic ---
    pdf_search_query = request.GET.get('pdf_q', '') # Use 'pdf_q' to avoid conflicts
    
    # Get base PDF list
    pdf_files = PDFFile.objects.filter(workspace=workspace)
    
    if pdf_search_query:
        # Filter by title if a query exists
        pdf_files = pdf_files.filter(title__icontains=pdf_search_query)
    # --- END UPDATE ---
    
    # Get public chat messages
    from chat.models import ChatMessage
    messages = ChatMessage.objects.filter(workspace=workspace).order_by('timestamp') # Added ordering
    
    # Get private AI chat messages
    ai_messages = AIChatMessage.objects.filter(
        workspace=workspace,
        user=request.user
    ).order_by('timestamp')

    # Get workspace members
    members = WorkspaceMember.objects.filter(workspace=workspace)
    
    # Get all users for invitation
    existing_member_ids = [m.user.id for m in members]
    available_users = User.objects.exclude(id__in=existing_member_ids + [request.user.id])
    
    return render(request, 'workspaces/workspace_detail.html', {
        'workspace': workspace,
        'pdf_files': pdf_files,
        'messages': messages,
        'ai_messages': ai_messages,
        'members': members,
        'available_users': available_users,
        'pdf_search_query': pdf_search_query, # Pass the query back to the template
        'current_user_role': current_user_role,  # Pass current user's role to template
        'is_researcher': current_user_role == WorkspaceMember.Role.RESEARCHER,  # Helper for template
        'is_creator': workspace.created_by == request.user,  # Helper for template - only creator can change roles
    })

@login_required
def invite_to_workspace_view(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)
    
    # Check if user is a member and has researcher role (only researchers can invite)
    try:
        user_membership = WorkspaceMember.objects.get(workspace=workspace, user=request.user)
        if user_membership.role != WorkspaceMember.Role.RESEARCHER:
            # Non-researchers cannot invite - redirect silently
            return redirect('workspace_detail', workspace_id=workspace.id)
    except WorkspaceMember.DoesNotExist:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        role_str = request.POST.get('role', WorkspaceMember.Role.REVIEWER)  # Default to REVIEWER if not provided
        
        # Validate role
        valid_roles = [WorkspaceMember.Role.RESEARCHER, WorkspaceMember.Role.REVIEWER]
        if role_str not in valid_roles:
            role_str = WorkspaceMember.Role.REVIEWER  # Fallback to REVIEWER if invalid
        
        if username:
            try:
                user = User.objects.get(username=username)
                # Check if already a member
                if not WorkspaceMember.objects.filter(workspace=workspace, user=user).exists():
                    WorkspaceMember.objects.create(
                        workspace=workspace, 
                        user=user,
                        role=role_str
                    )
            except User.DoesNotExist:
                pass
    
    return redirect('workspace_detail', workspace_id=workspace.id)

@login_required
@require_POST
def change_member_role_view(request, workspace_id):
    """Change the role of an existing workspace member. Only the workspace creator can change roles."""
    workspace = get_object_or_404(Workspace, id=workspace_id)
    
    # Check if user is the workspace creator (only creator can change roles)
    if workspace.created_by != request.user:
        # Non-creators cannot change roles - redirect silently
        return redirect('workspace_detail', workspace_id=workspace.id)
    
    # Verify user is a member of the workspace
    if not WorkspaceMember.objects.filter(workspace=workspace, user=request.user).exists():
        return redirect('dashboard')
    
    # Get the member whose role is being changed
    member_user_id = request.POST.get('member_user_id')
    new_role = request.POST.get('role')
    
    if not member_user_id or not new_role:
        return redirect('workspace_detail', workspace_id=workspace.id)
    
    # Validate role
    valid_roles = [WorkspaceMember.Role.RESEARCHER, WorkspaceMember.Role.REVIEWER]
    if new_role not in valid_roles:
        return redirect('workspace_detail', workspace_id=workspace.id)
    
    try:
        member_user = User.objects.get(id=member_user_id)
        # Get the membership to update
        member_membership = WorkspaceMember.objects.get(workspace=workspace, user=member_user)
        
        # Prevent user from changing their own role (optional safety check)
        # You can remove this if self-role-change should be allowed
        if member_user == request.user:
            return redirect('workspace_detail', workspace_id=workspace.id)
        
        # Update the role
        member_membership.role = new_role
        member_membership.save()
    except (User.DoesNotExist, WorkspaceMember.DoesNotExist):
        pass
    
    return redirect('workspace_detail', workspace_id=workspace.id)

@login_required
@require_POST  # Deletions must always be a POST request
def delete_workspace_view(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)
    
    # --- CRITICAL SECURITY CHECK ---
    # Only allow the creator of the workspace to delete it.
    if workspace.created_by != request.user:
        # Optionally, you could use Django messages to show an error
        return redirect('dashboard')

    # --- 1. Delete Physical Files ---
    
    # Delete the AI index folder (if it exists)
    if workspace.index_path and os.path.exists(workspace.index_path):
        try:
            shutil.rmtree(workspace.index_path)
            print(f"Deleted index folder: {workspace.index_path}")
        except Exception as e:
            print(f"Error deleting index folder: {e}")
            
    # PDF files are stored in database and will be automatically deleted
    # when the workspace is deleted (due to CASCADE)
    # No need to delete physical files anymore

    # --- 2. Delete the Workspace from Database ---
    # All related models (PDFFile, ChatMessage, AIChatMessage, WorkspaceMember)
    # will be automatically deleted because of 'on_delete=models.CASCADE'.
    workspace.delete()
    
    return redirect('dashboard')


# JSON API Views for frontend integration

@csrf_exempt  # TODO: Add proper CSRF handling in later step
def api_workspaces_view(request):
    """JSON API endpoint to list or create workspaces."""
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Authentication required"}, status=401)
    
    if request.method == 'GET':
        # List workspaces
        search_query = request.GET.get('q', '')
        workspaces = Workspace.objects.filter(members__user=request.user).distinct()
        
        if search_query:
            workspaces = workspaces.filter(name__icontains=search_query)
        
        # Serialize workspaces to JSON
        workspaces_data = []
        for workspace in workspaces:
            workspaces_data.append({
                "id": workspace.id,
                "name": workspace.name,
                "created_at": workspace.created_at.isoformat(),
                "created_by": workspace.created_by.username,
                "is_creator": workspace.created_by == request.user,
            })
        
        return JsonResponse({
            "success": True,
            "data": {"workspaces": workspaces_data}
        })
    
    elif request.method == 'POST':
        # Create workspace
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            
            if not name:
                return JsonResponse({"success": False, "message": "Workspace name is required"}, status=400)
            
            # Validate workspace name
            try:
                from .models import validate_workspace_name
                validate_workspace_name(name)
            except ValidationError as e:
                error_message = e.messages[0] if hasattr(e, 'messages') and e.messages else str(e)
                return JsonResponse({"success": False, "message": error_message}, status=400)
            
            if Workspace.objects.filter(members__user=request.user, name__iexact=name).exists():
                return JsonResponse({"success": False, "error": "Workspace with this name already exists."}, status=400)
            
            workspace = Workspace.objects.create(name=name, created_by=request.user)
            WorkspaceMember.objects.create(
                workspace=workspace,
                user=request.user,
                role=WorkspaceMember.Role.RESEARCHER
            )
            
            return JsonResponse({
                "success": True,
                "data": {
                    "workspace": {
                        "id": workspace.id,
                        "name": workspace.name,
                        "created_at": workspace.created_at.isoformat(),
                        "created_by": workspace.created_by.username,
                    }
                }
            }, status=201)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)
    
    else:
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)


@csrf_exempt
@login_required
@require_http_methods(["DELETE"])
def api_delete_workspace_view(request, workspace_id):
    """JSON API endpoint to delete a workspace."""
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Authentication required"}, status=401)
    
    try:
        workspace = get_object_or_404(Workspace, id=workspace_id)
        
        # Only allow the creator of the workspace to delete it
        if workspace.created_by != request.user:
            return JsonResponse({"success": False, "message": "Only the workspace creator can delete it"}, status=403)
        
        workspace_name = workspace.name
        workspace_members = list(WorkspaceMember.objects.filter(workspace=workspace).exclude(user=request.user))
        
        # Delete the AI index folder (if it exists)
        if workspace.index_path and os.path.exists(workspace.index_path):
            try:
                shutil.rmtree(workspace.index_path)
            except Exception as e:
                print(f"Error deleting index folder: {e}")
        
        # Notify all members (except the creator) before deleting
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        
        for member in workspace_members:
            notification = Notification.objects.create(
                user=member.user,
                type=Notification.NotificationType.WORKSPACE_DELETED,
                title="Workspace Deleted",
                message=f'The workspace "{workspace_name}" has been deleted by the creator.',
                related_workspace=None  # Workspace will be deleted, so don't set foreign key
            )
            
            unread_count = Notification.objects.filter(user=member.user, is_read=False).count()
            async_to_sync(channel_layer.group_send)(
                f"user_{member.user.id}",
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
        
        # Delete the workspace (CASCADE will handle related models)
        workspace.delete()
        
        return JsonResponse({"success": True, "message": "Workspace deleted successfully"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

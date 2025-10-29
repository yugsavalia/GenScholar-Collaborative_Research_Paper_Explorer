from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Workspace, WorkspaceMember


@login_required
def dashboard_view(request):
    # Get workspaces where user is a member
    workspaces = Workspace.objects.filter(members__user=request.user).distinct()
    return render(request, 'workspaces/dashboard.html', {'workspaces': workspaces})


@login_required
def create_workspace_view(request):
    if request.method == 'POST':
        name = request.POST['name']
        workspace = Workspace.objects.create(name=name, created_by=request.user)
        # Add creator as member
        WorkspaceMember.objects.create(workspace=workspace, user=request.user)
        return redirect('workspace_detail', workspace_id=workspace.id)
    
    return redirect('dashboard')


@login_required
def workspace_detail_view(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)
    
    # Check if user is a member
    if not WorkspaceMember.objects.filter(workspace=workspace, user=request.user).exists():
        return redirect('dashboard')
    
    # Get PDFs for this workspace
    from pdfs.models import PDFFile
    pdf_files = PDFFile.objects.filter(workspace=workspace)
    
    # Get chat messages
    from chat.models import ChatMessage
    messages = ChatMessage.objects.filter(workspace=workspace)[:50]
    
    # Get workspace members
    members = WorkspaceMember.objects.filter(workspace=workspace)
    
    # Get all users for invitation (excluding existing members and current user)
    existing_member_ids = [m.user.id for m in members]
    available_users = User.objects.exclude(id__in=existing_member_ids + [request.user.id])
    
    return render(request, 'workspaces/workspace_detail.html', {
        'workspace': workspace,
        'pdf_files': pdf_files,
        'messages': messages,
        'members': members,
        'available_users': available_users,
    })


@login_required
def invite_to_workspace_view(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)
    
    # Check if user is a member
    if not WorkspaceMember.objects.filter(workspace=workspace, user=request.user).exists():
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        if username:
            try:
                user = User.objects.get(username=username)
                # Check if already a member
                if not WorkspaceMember.objects.filter(workspace=workspace, user=user).exists():
                    WorkspaceMember.objects.create(workspace=workspace, user=user)
            except User.DoesNotExist:
                pass
    
    return redirect('workspace_detail', workspace_id=workspace.id)

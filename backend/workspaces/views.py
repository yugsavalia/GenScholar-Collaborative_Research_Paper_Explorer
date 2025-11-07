import os
import shutil
from django.conf import settings
from django.views.decorators.http import require_POST
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
    from pdf.models import PDFFile
    pdf_files = PDFFile.objects.filter(workspace=workspace)
    
    # Get public chat messages
    from chat.models import ChatMessage
    messages = ChatMessage.objects.filter(workspace=workspace)[:50]
    
    # Get private AI chat messages for *this user only*
    from chatbot.models import AIChatMessage
    ai_messages = AIChatMessage.objects.filter(
        workspace=workspace,
        user=request.user
    ).order_by('timestamp') # Get all messages in order
    
    # Get workspace members
    members = WorkspaceMember.objects.filter(workspace=workspace)
    
    # Get all users for invitation (excluding existing members and current user)
    existing_member_ids = [m.user.id for m in members]
    available_users = User.objects.exclude(id__in=existing_member_ids + [request.user.id])
   
    return render(request, 'workspaces/workspace_detail.html', {
        'workspace': workspace,
        'pdf_files': pdf_files,
        'messages': messages,
        'ai_messages': ai_messages, 
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
            
    # Delete all associated PDF files
    from pdfs.models import PDFFile
    pdf_files = PDFFile.objects.filter(workspace=workspace)
    for pdf in pdf_files:
        if os.path.exists(pdf.file.path):
            try:
                os.remove(pdf.file.path)
                print(f"Deleted PDF file: {pdf.file.path}")
            except Exception as e:
                print(f"Error deleting PDF file: {e}")

    # --- 2. Delete the Workspace from Database ---
    # All related models (PDFFile, ChatMessage, AIChatMessage, WorkspaceMember)
    # will be automatically deleted because of 'on_delete=models.CASCADE'.
    workspace.delete()
    
    return redirect('dashboard')
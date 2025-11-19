import os
import shutil
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound
from django.conf import settings
from workspaces.models import Workspace, WorkspaceMember
from .models import PDFFile
from django.views.decorators.http import require_POST

@login_required
def upload_pdf_view(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)
    
    # Check if user is a member
    if not WorkspaceMember.objects.filter(workspace=workspace, user=request.user).exists():
        return redirect('dashboard')
    
    if request.method == 'POST':
        title = request.POST['title']
        file = request.FILES['file']
        PDFFile.objects.create(
            workspace=workspace,
            uploaded_by=request.user,
            title=title,
            file=file
        )
    
    return redirect('workspace_detail', workspace_id=workspace.id)


@login_required
@require_POST  # Deletions must be POST requests
def delete_pdf_view(request, pdf_id):
    pdf = get_object_or_404(PDFFile, id=pdf_id)
    workspace = pdf.workspace
    
    # Security Check: Ensure the user is a member of the workspace
    if not WorkspaceMember.objects.filter(workspace=workspace, user=request.user).exists():
        return redirect('dashboard') # Or show an error

    try:
        # --- 1. Delete the physical PDF file ---
        if os.path.exists(pdf.file.path):
            os.remove(pdf.file.path)
            print(f"Deleted PDF file: {pdf.file.path}")

        # --- 2. Delete the entire workspace index ---
        if workspace.index_path and os.path.exists(workspace.index_path):
            shutil.rmtree(workspace.index_path)
            print(f"Deleted workspace index: {workspace.index_path}")

        # --- 3. Delete the PDF object from the database ---
        pdf.delete()

        # --- 4. Reset all other PDFs to be re-indexed ---
        remaining_pdfs = workspace.pdf_files.all()
        if remaining_pdfs.exists():
            remaining_pdfs.update(is_indexed=False)
            # Set status to NONE so the task processor knows to start from scratch
            workspace.processing_status = 'NONE'
        else:
            # No PDFs left, so no index
            workspace.processing_status = 'NONE'
            
        workspace.index_path = None
        workspace.save()
        
        # The background task will now re-build the index with the remaining PDFs
        
    except Exception as e:
        print(f"Error deleting PDF {pdf_id}: {e}")
        
    return redirect('workspace_detail', workspace_id=workspace.id)


@login_required
def view_pdf(request, pdf_id):
    pdf = get_object_or_404(PDFFile, id=pdf_id)
    
    # Security check: User must be a member
    if not WorkspaceMember.objects.filter(workspace=pdf.workspace, user=request.user).exists():
        return redirect('dashboard')
    
    # This is the correct, simple way.
    # It just redirects to the file's URL, which your JavaScript 'loadPDF(url)' expects.
    return redirect(pdf.file.url)
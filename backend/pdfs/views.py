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
    """(This view is correct, no changes needed)"""
    workspace = get_object_or_404(Workspace, id=workspace_id)
    
    # Check if user is a member
    if not WorkspaceMember.objects.filter(workspace=workspace, user=request.user).exists():
        return redirect('dashboard')
    
    if request.method == 'POST':
        title = request.POST['title']
        file = request.FILES['file']
        # Read file bytes and store in BinaryField
        pdf_bytes = file.read()
        PDFFile.objects.create(
            workspace=workspace,
            uploaded_by=request.user,
            title=title,
            file=pdf_bytes
        )
        # Assuming you have a post_save signal on PDFFile
        # that automatically queues the 'add_pdf_to_workspace_index' task.
    
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
        print(f"Deleting PDF {pdf_id} from Workspace {workspace.id}...")
        
        # --- 1. PDF bytes are stored in database and will be deleted automatically when PDFFile is deleted ---
        # No need to delete physical files anymore

        # --- 2. Delete the entire workspace index ---
        if workspace.index_path and os.path.exists(workspace.index_path):
            # Use shutil.rmtree since the index is a directory
            shutil.rmtree(workspace.index_path) 
            print(f"Deleted workspace index: {workspace.index_path}")

        # --- 3. Delete the PDF object from the database ---
        pdf.delete()
        print(f"Deleted PDF object {pdf_id} from database.")

        # --- 4. Reset all other PDFs to be re-indexed ---
        # Use the correct related_name, which we defined as 'pdf_files'
        remaining_pdfs = workspace.pdf_files.all()
        
        if remaining_pdfs.exists():
            print(f"Workspace {workspace.id} has {remaining_pdfs.count()} PDFs remaining.")
            
            # Mark all remaining PDFs to be re-indexed
            remaining_pdfs.update(is_indexed=False)
            
            # --- THIS IS THE FIX ---
            # Set status to PROCESSING. This tells the bot to wait
            # while your background tasks re-build the index.
            workspace.processing_status = Workspace.ProcessingStatus.PROCESSING
            print(f"Workspace {workspace.id} status set to PROCESSING for re-indexing.")
            
            # --- IMPORTANT ---
            # Your system must now automatically re-index the
            # PDFs that are marked 'is_indexed=False'.
            # If your 'post_save' signal doesn't do this,
            # you will need to loop and re-queue them manually here.
            
        else:
            # No PDFs left, so set status to NONE
            print(f"Workspace {workspace.id} has no PDFs left. Setting to NONE.")
            workspace.processing_status = Workspace.ProcessingStatus.NONE
            
        workspace.index_path = None
        workspace.save()
        
    except Exception as e:
        print(f"Error deleting PDF {pdf_id}: {e}")
        
    return redirect('workspace_detail', workspace_id=workspace.id)


@login_required
def view_pdf(request, pdf_id):
    """Return PDF bytes directly from database"""
    pdf = get_object_or_404(PDFFile, id=pdf_id)
    
    # Security check: User must be a member
    if not WorkspaceMember.objects.filter(workspace=pdf.workspace, user=request.user).exists():
        return redirect('dashboard')
    
    # Return PDF bytes directly from database
    from django.http import HttpResponse
    response = HttpResponse(pdf.file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{pdf.title}.pdf"'
    return response
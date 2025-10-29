import os
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotFound, FileResponse
from django.conf import settings
from workspaces.models import Workspace, WorkspaceMember
from .models import PDFFile


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
def serve_pdf_view(request, pdf_id):
    """Serve PDF file directly with proper headers for PDF.js"""
    pdf = get_object_or_404(PDFFile, id=pdf_id)
    
    # Check if user is a member of the workspace
    if not WorkspaceMember.objects.filter(workspace=pdf.workspace, user=request.user).exists():
        return HttpResponseNotFound("Access denied")
    
    try:
        file_path = pdf.file.path
        if not os.path.exists(file_path):
            return HttpResponseNotFound("PDF file not found")
        
        # Open file and create response
        file_handle = open(file_path, 'rb')
        response = FileResponse(
            file_handle,
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'inline; filename="{pdf.title}.pdf"'
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET'
        response['Access-Control-Allow-Headers'] = 'Range'
        response['Cache-Control'] = 'no-cache'
        response['Accept-Ranges'] = 'bytes'
        return response
    except Exception as e:
        return HttpResponseNotFound(f"Error serving PDF: {e}")


@login_required
def view_pdf_view(request, pdf_id):
    pdf = get_object_or_404(PDFFile, id=pdf_id)
    
    # Check if user is a member of the workspace
    if not WorkspaceMember.objects.filter(workspace=pdf.workspace, user=request.user).exists():
        return redirect('dashboard')
    
    from django.shortcuts import render
    
    try:
        # Use the full URL for PDF.js
        pdf_url = request.build_absolute_uri(f'/pdfs/{pdf_id}/serve/')
        
        context = {
            'pdf_url': pdf_url,
            'pdf_title': pdf.title
        }
        
        return render(request, 'pdfs/pdf_viewer.html', context)
    except Exception as e:
        return HttpResponseNotFound(f"PDF file not found: {e}")

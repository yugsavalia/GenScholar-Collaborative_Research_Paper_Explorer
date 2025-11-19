from django.urls import path
from . import views

urlpatterns = [
    # Path for uploading a PDF to a workspace
    path('workspace/<int:workspace_id>/upload/', views.upload_pdf_view, name='upload_pdf'),
    
    # Path for deleting a PDF
    path('<int:pdf_id>/delete/', views.delete_pdf_view, name='delete_pdf'),
    
    # Path for viewing a PDF (this is the fix)
    path('<int:pdf_id>/view/', views.view_pdf, name='view_pdf'),
]
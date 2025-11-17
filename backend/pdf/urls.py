from django.urls import path
from . import views

urlpatterns = [
    path('workspace/<int:workspace_id>/upload/', views.upload_pdf_view, name='upload_pdf'),
    path('<int:pdf_id>/view/', views.view_pdf_view, name='view_pdf'),
    path('<int:pdf_id>/serve/', views.serve_pdf_view, name='serve_pdf'),
    path('<int:pdf_id>/delete/', views.delete_pdf_view, name='delete_pdf'),

]




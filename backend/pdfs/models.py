from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from workspaces.models import Workspace


class PDFFile(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='pdf_files')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_pdfs')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='pdfs/')
    uploaded_at = models.DateTimeField(default=timezone.now)
    
    # --- MODIFIED FIELDS FOR CHATBOT ---
    
    # This simple flag will be True when the PDF's
    # content has been added to the workspace's main index.
    is_indexed = models.BooleanField(default=False)
    
    # --- END MODIFIED FIELDS ---
    
    def __str__(self):
        return self.title


class Annotation(models.Model):
    """Represents an annotation on a PDF page."""
    pdf = models.ForeignKey(PDFFile, on_delete=models.CASCADE, related_name='annotations')
    page_number = models.PositiveIntegerField()
    coordinates = models.JSONField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pdf_annotations'
    )
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Annotation on {self.pdf.title} (page {self.page_number})"
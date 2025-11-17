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
    is_indexed = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title

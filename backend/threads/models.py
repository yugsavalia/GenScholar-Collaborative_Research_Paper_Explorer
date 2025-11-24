from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from workspaces.models import Workspace
from pdfs.models import PDFFile


class Thread(models.Model):
    """A threaded discussion anchored to a specific text selection in a PDF."""
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='threads')
    pdf = models.ForeignKey(PDFFile, on_delete=models.CASCADE, related_name='threads')
    page_number = models.PositiveIntegerField(help_text="Page number where the selection is located")
    selection_text = models.TextField(help_text="The selected text that started this thread")
    
    # Anchor position - stored as normalized coordinates (0-1) relative to page dimensions
    # Format: {x: float, y: float, width: float, height: float}
    # Coordinates are normalized to page width/height for persistence across screen sizes
    anchor_rect = models.JSONField(
        help_text="Bounding box of the selection in normalized coordinates (0-1)"
    )
    
    # Optional: which side of selection to place icon ('left' or 'right')
    anchor_side = models.CharField(
        max_length=10,
        choices=[('left', 'Left'), ('right', 'Right')],
        default='right',
        help_text="Which side of the selection to place the anchor icon"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_threads'
    )
    created_at = models.DateTimeField(default=timezone.now)
    last_activity_at = models.DateTimeField(auto_now=True, help_text="Updated when a new message is added")
    
    class Meta:
        ordering = ['-last_activity_at']
        indexes = [
            models.Index(fields=['pdf', 'page_number']),  # Fast lookup by PDF and page
            models.Index(fields=['workspace', 'pdf']),     # Fast lookup by workspace and PDF
        ]
    
    def __str__(self):
        return f"Thread on {self.pdf.title} (page {self.page_number}): {self.selection_text[:50]}"


class Message(models.Model):
    """A message in a threaded discussion."""
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='thread_messages'
    )
    content = models.TextField(help_text="Message content")
    created_at = models.DateTimeField(default=timezone.now)
    edited_at = models.DateTimeField(null=True, blank=True, help_text="When the message was last edited")
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['thread', 'created_at']),  # Fast lookup by thread and time
        ]
    
    def __str__(self):
        sender_name = self.sender.username if self.sender else "Unknown"
        return f"{sender_name}: {self.content[:50]}"


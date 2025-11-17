from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Workspace(models.Model):
    name = models.CharField(max_length=200)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_workspaces')
    created_at = models.DateTimeField(default=timezone.now)

    # --- ADD THESE NEW FIELDS ---

    class ProcessingStatus(models.TextChoices):
        """Defines the stages of AI processing for the *workspace* index."""
        READY = 'READY', 'Ready'           # The index is ready to be queried
        PROCESSING = 'PROCESSING', 'Processing' # A PDF is currently being added
        FAILED = 'FAILED', 'Failed'         # An error occurred
        NONE = 'NONE', 'None'             # No index exists yet (or no PDFs)

    # Tracks the status of the *workspace's* main index
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.NONE
    )
    
    # Stores the file path to the *single* FAISS index for this workspace
    index_path = models.CharField(max_length=512, blank=True, null=True)
    
    # --- END NEW FIELDS ---
    
    def __str__(self):
        return self.name


class WorkspaceMember(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workspace_memberships')
    joined_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['workspace', 'user']
    
    def __str__(self):
        return f"{self.user.username} in {self.workspace.name}"
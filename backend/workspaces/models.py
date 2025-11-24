import re
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError


def validate_workspace_name(name):
    """Validate workspace name according to strict rules."""
    if len(name) > 25:
        raise ValidationError("Max size is 25 characters")
    
    # cannot start with a space
    if name.startswith(" "):
        raise ValidationError("Workspace name cannot start with a blank space.")
    
    # cannot start with an underscore
    if name.startswith("_"):
        raise ValidationError("Workspace name cannot start with an underscore.")
    
    # cannot start with a digit
    if name and name[0].isdigit():
        raise ValidationError("Workspace name cannot start with a digit.")
    
    # must start with a letter
    if name and not name[0].isalpha():
        raise ValidationError("Workspace name cannot start with a digit, underscore, or blank space.")
    
    # allowed characters: letters, digits, underscores, spaces
    if not re.match(r'^[A-Za-z0-9_ ]+$', name):
        raise ValidationError(
            "Workspace name may contain only letters, digits, underscores, and spaces."
        )


class Workspace(models.Model):
    name = models.CharField(max_length=200, validators=[validate_workspace_name])
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_workspaces')
    created_at = models.DateTimeField(default=timezone.now)
    
    def clean(self):
        """Validate workspace name on model clean."""
        super().clean()
        if self.name:
            validate_workspace_name(self.name.strip())
    
    def save(self, *args, **kwargs):
        """Override save to call clean validation."""
        self.full_clean()
        super().save(*args, **kwargs)

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
    """Represents a user's membership in a workspace with a specific role."""
    
    class Role(models.TextChoices):
        """Defines the roles a user can have in a workspace."""
        RESEARCHER = 'RESEARCHER', 'Researcher'
        REVIEWER = 'REVIEWER', 'Reviewer'
    
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workspace_memberships')
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.RESEARCHER,
        help_text="The role of this user in the workspace"
    )
    joined_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['workspace', 'user']
    
    def __str__(self):
        return f"{self.user.username} ({self.role}) in {self.workspace.name}"


class WorkspaceInvitation(models.Model):
    """Represents a pending invitation to join a workspace."""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        DECLINED = 'DECLINED', 'Declined'
    
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='invitations')
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invitations')
    role = models.CharField(
        max_length=20,
        choices=WorkspaceMember.Role.choices,
        default=WorkspaceMember.Role.REVIEWER,
        help_text="The role to assign when invitation is accepted"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    created_at = models.DateTimeField(default=timezone.now)
    responded_at = models.DateTimeField(null=True, blank=True, help_text="When the invitation was accepted or declined")
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Optional expiration date")
    
    class Meta:
        # Duplicate pending invitations are prevented in the view logic
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invitation for {self.invited_user.username} to {self.workspace.name} ({self.status})"


class Notification(models.Model):
    """In-app notifications for users."""
    
    class NotificationType(models.TextChoices):
        INVITATION = 'INVITATION', 'Invitation'
        ROLE_CHANGED = 'ROLE_CHANGED', 'Role Changed'
        MEMBER_ADDED = 'MEMBER_ADDED', 'Member Added'
        WORKSPACE_DELETED = 'WORKSPACE_DELETED', 'Workspace Deleted'
        MENTION = 'MENTION', 'Mention'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NotificationType.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    related_invitation = models.ForeignKey(
        WorkspaceInvitation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.type} notification for {self.user.username}: {self.title}"


class PinnedNote(models.Model):
    """A pinned note for a workspace - one per workspace."""
    workspace = models.OneToOneField(Workspace, on_delete=models.CASCADE, related_name='pinned_note')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pinned_notes')
    content = models.TextField(blank=True, max_length=10000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"PinnedNote({self.workspace_id})"
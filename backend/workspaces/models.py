from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Workspace(models.Model):
    name = models.CharField(max_length=200)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_workspaces')
    created_at = models.DateTimeField(default=timezone.now)
    
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

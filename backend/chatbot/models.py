from django.db import models
from django.contrib.auth.models import User
from workspaces.models import Workspace

class AIChatMessage(models.Model):
    """
    Stores a single private AI chat message, linked to a user and workspace.
    """
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='ai_messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_messages')
    message = models.TextField()
    is_from_bot = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        actor = "AI_Bot" if self.is_from_bot else self.user.username
        return f"{actor}: {self.message[:50]}"
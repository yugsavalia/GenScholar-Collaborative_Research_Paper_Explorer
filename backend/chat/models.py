from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from workspaces.models import Workspace


class ChatMessage(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}"

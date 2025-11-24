"""
Comprehensive tests for chat app.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from workspaces.models import Workspace
from .models import ChatMessage


class ChatMessageModelTestCase(TestCase):
    """Test ChatMessage model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            created_by=self.user
        )
    
    def test_chat_message_creation(self):
        """Test chat message can be created."""
        message = ChatMessage.objects.create(
            workspace=self.workspace,
            user=self.user,
            message='Test message'
        )
        self.assertIsNotNone(message.id)
        self.assertEqual(message.workspace, self.workspace)
        self.assertEqual(message.user, self.user)
        self.assertEqual(message.message, 'Test message')
    
    def test_chat_message_str(self):
        """Test chat message string representation."""
        message = ChatMessage.objects.create(
            workspace=self.workspace,
            user=self.user,
            message='Test message'
        )
        expected = f"{self.user.username}: Test message"
        self.assertEqual(str(message), expected)
    
    def test_chat_message_ordering(self):
        """Test chat messages are ordered by timestamp."""
        message1 = ChatMessage.objects.create(
            workspace=self.workspace,
            user=self.user,
            message='First message'
        )
        message2 = ChatMessage.objects.create(
            workspace=self.workspace,
            user=self.user,
            message='Second message'
        )
        messages = list(ChatMessage.objects.all())
        self.assertEqual(messages[0], message1)
        self.assertEqual(messages[1], message2)

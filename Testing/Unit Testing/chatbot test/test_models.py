"""
Comprehensive tests for chatbot app.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from workspaces.models import Workspace, WorkspaceMember
from .models import AIChatMessage


class AIChatMessageModelTestCase(TestCase):
    """Test AIChatMessage model."""
    
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
    
    def test_ai_chat_message_creation_user(self):
        """Test AI chat message can be created from user."""
        message = AIChatMessage.objects.create(
            workspace=self.workspace,
            user=self.user,
            message='User question',
            is_from_bot=False
        )
        self.assertIsNotNone(message.id)
        self.assertEqual(message.message, 'User question')
        self.assertFalse(message.is_from_bot)
    
    def test_ai_chat_message_creation_bot(self):
        """Test AI chat message can be created from bot."""
        message = AIChatMessage.objects.create(
            workspace=self.workspace,
            user=self.user,
            message='Bot response',
            is_from_bot=True
        )
        self.assertIsNotNone(message.id)
        self.assertEqual(message.message, 'Bot response')
        self.assertTrue(message.is_from_bot)
    
    def test_ai_chat_message_str_user(self):
        """Test AI chat message string representation for user message."""
        message = AIChatMessage.objects.create(
            workspace=self.workspace,
            user=self.user,
            message='User question',
            is_from_bot=False
        )
        expected = f"{self.user.username}: User question"
        self.assertEqual(str(message), expected)
    
    def test_ai_chat_message_str_bot(self):
        """Test AI chat message string representation for bot message."""
        message = AIChatMessage.objects.create(
            workspace=self.workspace,
            user=self.user,
            message='Bot response',
            is_from_bot=True
        )
        expected = "AI_Bot: Bot response"
        self.assertEqual(str(message), expected)
    
    def test_ai_chat_message_default_is_from_bot(self):
        """Test is_from_bot defaults to False."""
        message = AIChatMessage.objects.create(
            workspace=self.workspace,
            user=self.user,
            message='Test message'
        )
        self.assertFalse(message.is_from_bot)
    
    def test_ai_chat_message_ordering(self):
        """Test AI chat messages are ordered by timestamp."""
        message1 = AIChatMessage.objects.create(
            workspace=self.workspace,
            user=self.user,
            message='First message',
            is_from_bot=False
        )
        message2 = AIChatMessage.objects.create(
            workspace=self.workspace,
            user=self.user,
            message='Second message',
            is_from_bot=True
        )
        messages = list(AIChatMessage.objects.all())
        self.assertEqual(messages[0], message1)
        self.assertEqual(messages[1], message2)

"""
Tests for threads serializers.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from workspaces.models import Workspace, WorkspaceMember
from pdfs.models import PDFFile
from .models import Thread, Message
from .serializers import (
    ThreadSerializer, ThreadDetailSerializer, CreateThreadSerializer,
    MessageSerializer, CreateMessageSerializer
)


class ThreadSerializerTestCase(TestCase):
    """Test thread serializers."""
    
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
        self.pdf = PDFFile.objects.create(
            workspace=self.workspace,
            uploaded_by=self.user,
            title='Test PDF',
            file=b'%PDF-1.4 fake pdf content'
        )
        self.thread = Thread.objects.create(
            workspace=self.workspace,
            pdf=self.pdf,
            page_number=1,
            selection_text='Selected text',
            anchor_rect={'x': 0.1, 'y': 0.2, 'width': 0.3, 'height': 0.4},
            created_by=self.user
        )
    
    def test_thread_serializer(self):
        """Test ThreadSerializer."""
        serializer = ThreadSerializer(self.thread)
        data = serializer.data
        self.assertEqual(data['id'], self.thread.id)
        self.assertEqual(data['page_number'], 1)
        self.assertEqual(data['selection_text'], 'Selected text')
        self.assertIn('message_count', data)
        self.assertIn('last_message_preview', data)
    
    def test_thread_serializer_with_messages(self):
        """Test ThreadSerializer with messages."""
        Message.objects.create(
            thread=self.thread,
            sender=self.user,
            content='Test message'
        )
        serializer = ThreadSerializer(self.thread)
        data = serializer.data
        self.assertEqual(data['message_count'], 1)
        self.assertIsNotNone(data['last_message_preview'])
    
    def test_thread_detail_serializer(self):
        """Test ThreadDetailSerializer."""
        Message.objects.create(
            thread=self.thread,
            sender=self.user,
            content='Test message'
        )
        serializer = ThreadDetailSerializer(self.thread)
        data = serializer.data
        self.assertIn('messages', data)
        self.assertEqual(len(data['messages']), 1)
    
    def test_create_thread_serializer_valid(self):
        """Test CreateThreadSerializer with valid data."""
        data = {
            'pdf': self.pdf.id,
            'page_number': 1,
            'selection_text': 'Selected text',
            'anchor_rect': {'x': 0.1, 'y': 0.2, 'width': 0.3, 'height': 0.4},
            'anchor_side': 'right'
        }
        serializer = CreateThreadSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_create_thread_serializer_invalid_anchor_rect(self):
        """Test CreateThreadSerializer with invalid anchor_rect."""
        data = {
            'pdf': self.pdf.id,
            'page_number': 1,
            'selection_text': 'Selected text',
            'anchor_rect': {'x': 0.1},  # Missing required keys
        }
        serializer = CreateThreadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
    
    def test_create_thread_serializer_anchor_rect_out_of_range(self):
        """Test CreateThreadSerializer with anchor_rect out of range."""
        data = {
            'pdf': self.pdf.id,
            'page_number': 1,
            'selection_text': 'Selected text',
            'anchor_rect': {'x': 2.0, 'y': 0.2, 'width': 0.3, 'height': 0.4},  # x > 1
        }
        serializer = CreateThreadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
    
    def test_create_thread_serializer_anchor_rect_invalid_type(self):
        """Test CreateThreadSerializer with anchor_rect invalid type."""
        data = {
            'pdf': self.pdf.id,
            'page_number': 1,
            'selection_text': 'Selected text',
            'anchor_rect': {'x': 'invalid', 'y': 0.2, 'width': 0.3, 'height': 0.4},
        }
        serializer = CreateThreadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
    
    def test_create_thread_serializer_anchor_rect_not_dict(self):
        """Test CreateThreadSerializer with anchor_rect not a dict."""
        data = {
            'pdf': self.pdf.id,
            'page_number': 1,
            'selection_text': 'Selected text',
            'anchor_rect': 'not a dict',
        }
        serializer = CreateThreadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
    
    def test_create_thread_serializer_empty_selection_text(self):
        """Test CreateThreadSerializer with empty selection_text."""
        data = {
            'pdf': self.pdf.id,
            'page_number': 1,
            'selection_text': '',
            'anchor_rect': {'x': 0.1, 'y': 0.2, 'width': 0.3, 'height': 0.4},
        }
        serializer = CreateThreadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
    
    def test_create_thread_serializer_long_selection_text(self):
        """Test CreateThreadSerializer with too long selection_text."""
        data = {
            'pdf': self.pdf.id,
            'page_number': 1,
            'selection_text': 'x' * 1001,  # Too long
            'anchor_rect': {'x': 0.1, 'y': 0.2, 'width': 0.3, 'height': 0.4},
        }
        serializer = CreateThreadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
    
    def test_message_serializer(self):
        """Test MessageSerializer."""
        message = Message.objects.create(
            thread=self.thread,
            sender=self.user,
            content='Test message'
        )
        serializer = MessageSerializer(message)
        data = serializer.data
        self.assertEqual(data['id'], message.id)
        self.assertEqual(data['content'], 'Test message')
        self.assertIn('sender', data)
    
    def test_create_message_serializer_valid(self):
        """Test CreateMessageSerializer with valid data."""
        data = {'content': 'Test message'}
        serializer = CreateMessageSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_create_message_serializer_empty_content(self):
        """Test CreateMessageSerializer with empty content."""
        data = {'content': ''}
        serializer = CreateMessageSerializer(data=data)
        self.assertFalse(serializer.is_valid())
    
    def test_create_message_serializer_long_content(self):
        """Test CreateMessageSerializer with too long content."""
        data = {'content': 'x' * 5001}  # Too long
        serializer = CreateMessageSerializer(data=data)
        self.assertFalse(serializer.is_valid())


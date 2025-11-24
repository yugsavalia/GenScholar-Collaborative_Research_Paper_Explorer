"""
Comprehensive tests for threads app.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from workspaces.models import Workspace, WorkspaceMember
from pdfs.models import PDFFile
from .models import Thread, Message


class ThreadModelTestCase(TestCase):
    """Test Thread model."""
    
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
    
    def test_thread_creation(self):
        """Test thread can be created."""
        thread = Thread.objects.create(
            workspace=self.workspace,
            pdf=self.pdf,
            page_number=1,
            selection_text='Selected text',
            anchor_rect={'x': 0.1, 'y': 0.2, 'width': 0.3, 'height': 0.4},
            anchor_side='right',
            created_by=self.user
        )
        self.assertIsNotNone(thread.id)
        self.assertEqual(thread.workspace, self.workspace)
        self.assertEqual(thread.pdf, self.pdf)
        self.assertEqual(thread.page_number, 1)
        self.assertEqual(thread.selection_text, 'Selected text')
        self.assertEqual(thread.anchor_side, 'right')
    
    def test_thread_str(self):
        """Test thread string representation."""
        thread = Thread.objects.create(
            workspace=self.workspace,
            pdf=self.pdf,
            page_number=1,
            selection_text='Selected text',
            anchor_rect={'x': 0.1, 'y': 0.2},
            created_by=self.user
        )
        expected = f"Thread on {self.pdf.title} (page 1): Selected text"
        self.assertEqual(str(thread), expected)
    
    def test_thread_default_anchor_side(self):
        """Test default anchor_side is 'right'."""
        thread = Thread.objects.create(
            workspace=self.workspace,
            pdf=self.pdf,
            page_number=1,
            selection_text='Selected text',
            anchor_rect={'x': 0.1, 'y': 0.2}
        )
        self.assertEqual(thread.anchor_side, 'right')
    
    def test_thread_ordering(self):
        """Test threads are ordered by last_activity_at."""
        from django.utils import timezone
        import time
        
        thread1 = Thread.objects.create(
            workspace=self.workspace,
            pdf=self.pdf,
            page_number=1,
            selection_text='First',
            anchor_rect={'x': 0.1, 'y': 0.2}
        )
        # Add a small delay to ensure different timestamps
        time.sleep(0.01)
        thread2 = Thread.objects.create(
            workspace=self.workspace,
            pdf=self.pdf,
            page_number=1,
            selection_text='Second',
            anchor_rect={'x': 0.1, 'y': 0.2}
        )
        threads = list(Thread.objects.all())
        # Most recent first (ordered by -last_activity_at)
        self.assertEqual(threads[0], thread2)
        self.assertEqual(threads[1], thread1)


class MessageModelTestCase(TestCase):
    """Test Message model."""
    
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
            anchor_rect={'x': 0.1, 'y': 0.2},
            created_by=self.user
        )
    
    def test_message_creation(self):
        """Test message can be created."""
        message = Message.objects.create(
            thread=self.thread,
            sender=self.user,
            content='Test message content'
        )
        self.assertIsNotNone(message.id)
        self.assertEqual(message.thread, self.thread)
        self.assertEqual(message.sender, self.user)
        self.assertEqual(message.content, 'Test message content')
    
    def test_message_str(self):
        """Test message string representation."""
        message = Message.objects.create(
            thread=self.thread,
            sender=self.user,
            content='Test message'
        )
        expected = f"{self.user.username}: Test message"
        self.assertEqual(str(message), expected)
    
    def test_message_without_sender(self):
        """Test message can be created without sender."""
        message = Message.objects.create(
            thread=self.thread,
            content='Anonymous message'
        )
        self.assertIsNone(message.sender)
        self.assertEqual(str(message), "Unknown: Anonymous message")
    
    def test_message_ordering(self):
        """Test messages are ordered by created_at."""
        message1 = Message.objects.create(
            thread=self.thread,
            sender=self.user,
            content='First message'
        )
        message2 = Message.objects.create(
            thread=self.thread,
            sender=self.user,
            content='Second message'
        )
        messages = list(Message.objects.all())
        self.assertEqual(messages[0], message1)
        self.assertEqual(messages[1], message2)


class ThreadViewSetTestCase(TestCase):
    """Test ThreadViewSet."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            created_by=self.user
        )
        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.user,
            role=WorkspaceMember.Role.RESEARCHER
        )
        self.pdf = PDFFile.objects.create(
            workspace=self.workspace,
            uploaded_by=self.user,
            title='Test PDF',
            file=b'%PDF-1.4 fake pdf content'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_threads(self):
        """Test list threads."""
        Thread.objects.create(
            workspace=self.workspace,
            pdf=self.pdf,
            page_number=1,
            selection_text='Selected text',
            anchor_rect={'x': 0.1, 'y': 0.2},
            created_by=self.user
        )
        response = self.client.get(
            f'/api/threads/?workspace_id={self.workspace.id}&pdf_id={self.pdf.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_list_threads_missing_params(self):
        """Test list threads with missing parameters."""
        response = self.client.get('/api/threads/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_thread(self):
        """Test create thread."""
        response = self.client.post('/api/threads/', {
            'workspace_id': self.workspace.id,
            'pdf_id': self.pdf.id,
            'page_number': 1,
            'selection_text': 'Selected text',
            'anchor_rect': {'x': 0.1, 'y': 0.2, 'width': 0.3, 'height': 0.4},
            'anchor_side': 'right'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Thread.objects.filter(pdf=self.pdf).exists())
    
    def test_retrieve_thread(self):
        """Test retrieve thread."""
        thread = Thread.objects.create(
            workspace=self.workspace,
            pdf=self.pdf,
            page_number=1,
            selection_text='Selected text',
            anchor_rect={'x': 0.1, 'y': 0.2},
            created_by=self.user
        )
        response = self.client.get(f'/api/threads/{thread.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_add_message_to_thread(self):
        """Test add message to thread."""
        thread = Thread.objects.create(
            workspace=self.workspace,
            pdf=self.pdf,
            page_number=1,
            selection_text='Selected text',
            anchor_rect={'x': 0.1, 'y': 0.2},
            created_by=self.user
        )
        response = self.client.post(f'/api/threads/{thread.id}/messages/', {
            'content': 'Test message'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Message.objects.filter(thread=thread).exists())
    
    def test_get_messages_for_thread(self):
        """Test get messages for thread."""
        thread = Thread.objects.create(
            workspace=self.workspace,
            pdf=self.pdf,
            page_number=1,
            selection_text='Selected text',
            anchor_rect={'x': 0.1, 'y': 0.2},
            created_by=self.user
        )
        Message.objects.create(
            thread=thread,
            sender=self.user,
            content='Test message'
        )
        response = self.client.get(f'/api/threads/{thread.id}/get_messages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


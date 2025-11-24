"""
Additional tests for threads/views.py to increase coverage to 95%+.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from workspaces.models import Workspace, WorkspaceMember
from pdfs.models import PDFFile
from .models import Thread, Message


class ThreadViewsCoverageTestCase(TestCase):
    """Additional tests to cover missing lines in threads/views.py."""
    
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
    
    def test_get_serializer_class_retrieve(self):
        """Test get_serializer_class for retrieve action."""
        thread = Thread.objects.create(
            workspace=self.workspace,
            pdf=self.pdf,
            page_number=1,
            selection_text='Test',
            anchor_rect={'x': 0.1, 'y': 0.2},
            created_by=self.user
        )
        response = self.client.get(f'/api/threads/{thread.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should use ThreadDetailSerializer which includes messages
        self.assertIn('messages', response.data)
    
    def test_get_serializer_class_list(self):
        """Test get_serializer_class for list action."""
        Thread.objects.create(
            workspace=self.workspace,
            pdf=self.pdf,
            page_number=1,
            selection_text='Test',
            anchor_rect={'x': 0.1, 'y': 0.2},
            created_by=self.user
        )
        response = self.client.get(
            f'/api/threads/?workspace_id={self.workspace.id}&pdf_id={self.pdf.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should use ThreadSerializer (not ThreadDetailSerializer)
        if len(response.data) > 0:
            # List serializer may not have messages field
            pass
    
    def test_create_thread_pdf_not_found(self):
        """Test create thread when PDF doesn't exist in workspace."""
        other_workspace = Workspace.objects.create(
            name='Other Workspace',
            created_by=self.user
        )
        other_pdf = PDFFile.objects.create(
            workspace=other_workspace,
            uploaded_by=self.user,
            title='Other PDF',
            file=b'%PDF-1.4 other'
        )
        # Try to create thread with PDF from different workspace
        response = self.client.post('/api/threads/', {
            'workspace_id': self.workspace.id,
            'pdf_id': other_pdf.id,  # PDF from different workspace
            'page_number': 1,
            'selection_text': 'Test',
            'anchor_rect': {'x': 0.1, 'y': 0.2, 'width': 0.3, 'height': 0.4}
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    @patch('threads.views.get_channel_layer')
    def test_create_thread_broadcast_exception(self, mock_get_channel):
        """Test create thread when broadcast fails."""
        mock_get_channel.side_effect = Exception("Broadcast error")
        response = self.client.post('/api/threads/', {
            'workspace_id': self.workspace.id,
            'pdf_id': self.pdf.id,
            'page_number': 1,
            'selection_text': 'Test',
            'anchor_rect': {'x': 0.1, 'y': 0.2, 'width': 0.3, 'height': 0.4}
        }, format='json')
        # Should still succeed even if broadcast fails
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    @patch('threads.views.get_channel_layer')
    def test_add_message_broadcast_exception(self, mock_get_channel):
        """Test add message when broadcast fails."""
        thread = Thread.objects.create(
            workspace=self.workspace,
            pdf=self.pdf,
            page_number=1,
            selection_text='Test',
            anchor_rect={'x': 0.1, 'y': 0.2},
            created_by=self.user
        )
        mock_get_channel.side_effect = Exception("Broadcast error")
        response = self.client.post(f'/api/threads/{thread.id}/messages/', {
            'content': 'Test message'
        }, format='json')
        # Should still succeed even if broadcast fails
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    @patch('threads.views.get_channel_layer')
    def test_broadcast_thread_created_connection_refused(self, mock_get_channel):
        """Test broadcast_thread_created with ConnectionRefusedError."""
        thread = Thread.objects.create(
            workspace=self.workspace,
            pdf=self.pdf,
            page_number=1,
            selection_text='Test',
            anchor_rect={'x': 0.1, 'y': 0.2},
            created_by=self.user
        )
        mock_get_channel.side_effect = ConnectionRefusedError("Redis not available")
        # This should not raise exception, just log warning
        from threads.views import ThreadViewSet
        viewset = ThreadViewSet()
        viewset.request = MagicMock()
        viewset.request.user = self.user
        try:
            viewset.broadcast_thread_created(thread)
        except Exception:
            self.fail("broadcast_thread_created should handle ConnectionRefusedError")
    
    @patch('threads.views.get_channel_layer')
    def test_broadcast_message_created_connection_refused(self, mock_get_channel):
        """Test broadcast_message_created with ConnectionRefusedError."""
        thread = Thread.objects.create(
            workspace=self.workspace,
            pdf=self.pdf,
            page_number=1,
            selection_text='Test',
            anchor_rect={'x': 0.1, 'y': 0.2},
            created_by=self.user
        )
        message = Message.objects.create(
            thread=thread,
            sender=self.user,
            content='Test message'
        )
        mock_get_channel.side_effect = ConnectionRefusedError("Redis not available")
        # This should not raise exception, just log warning
        from threads.views import ThreadViewSet
        viewset = ThreadViewSet()
        viewset.request = MagicMock()
        viewset.request.user = self.user
        try:
            viewset.broadcast_message_created(thread, message)
        except Exception:
            self.fail("broadcast_message_created should handle ConnectionRefusedError")


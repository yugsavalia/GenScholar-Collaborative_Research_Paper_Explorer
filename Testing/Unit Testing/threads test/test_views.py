"""
More tests for threads views to increase coverage.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from workspaces.models import Workspace, WorkspaceMember
from pdfs.models import PDFFile
from .models import Thread, Message
from unittest.mock import patch, MagicMock


class ThreadViewSetMoreTestCase(TestCase):
    """More tests for ThreadViewSet."""
    
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
        self.thread = Thread.objects.create(
            workspace=self.workspace,
            pdf=self.pdf,
            page_number=1,
            selection_text='Selected text',
            anchor_rect={'x': 0.1, 'y': 0.2, 'width': 0.3, 'height': 0.4},
            created_by=self.user
        )
    
    def test_get_serializer_class_list(self):
        """Test get_serializer_class for list action."""
        response = self.client.get(
            f'/api/threads/?workspace_id={self.workspace.id}&pdf_id={self.pdf.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should use ThreadSerializer for list
        # Verify response contains thread data
        self.assertIsInstance(response.data, list)
    
    def test_get_serializer_class_create(self):
        """Test get_serializer_class for create action - uses CreateThreadSerializer."""
        response = self.client.post('/api/threads/', {
            'workspace_id': self.workspace.id,
            'pdf_id': self.pdf.id,
            'page_number': 1,
            'selection_text': 'New thread',
            'anchor_rect': {'x': 0.1, 'y': 0.2, 'width': 0.3, 'height': 0.4}
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Verify thread was created
        self.assertTrue(Thread.objects.filter(selection_text='New thread').exists())
    
    def test_broadcast_thread_created_exception(self):
        """Test broadcast_thread_created with exception."""
        # Create thread - broadcast might fail but shouldn't break request
        with patch('threads.views.get_channel_layer') as mock_get_channel:
            # Make get_channel_layer raise an exception
            mock_get_channel.side_effect = Exception("Channel error")
            response = self.client.post('/api/threads/', {
                'workspace_id': self.workspace.id,
                'pdf_id': self.pdf.id,
                'page_number': 1,
                'selection_text': 'New thread with exception',
                'anchor_rect': {'x': 0.1, 'y': 0.2, 'width': 0.3, 'height': 0.4}
            }, format='json')
            # Should still succeed even if broadcast fails
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            # Verify thread was created despite broadcast failure
            self.assertTrue(Thread.objects.filter(selection_text='New thread with exception').exists())
    
    def test_broadcast_message_created_exception(self):
        """Test broadcast_message_created with exception."""
        # Add message - broadcast might fail but shouldn't break request
        with patch('threads.views.get_channel_layer') as mock_get_channel:
            # Make get_channel_layer raise an exception
            mock_get_channel.side_effect = Exception("Channel error")
            response = self.client.post(f'/api/threads/{self.thread.id}/messages/', {
                'content': 'Test message with exception'
            }, format='json')
            # Should still succeed even if broadcast fails
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            # Verify message was created despite broadcast failure
            self.assertTrue(Message.objects.filter(content='Test message with exception').exists())
    
    def test_create_thread_workspace_id_in_query_params(self):
        """Test create thread with workspace_id in query params."""
        response = self.client.post(
            f'/api/threads/?workspace_id={self.workspace.id}',
            {
                'pdf_id': self.pdf.id,
                'page_number': 1,
                'selection_text': 'New thread',
                'anchor_rect': {'x': 0.1, 'y': 0.2, 'width': 0.3, 'height': 0.4}
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


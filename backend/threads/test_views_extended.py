"""
Extended tests for threads views.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from workspaces.models import Workspace, WorkspaceMember
from pdfs.models import PDFFile
from .models import Thread, Message


class ThreadViewSetExtendedTestCase(TestCase):
    """Extended tests for ThreadViewSet."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
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
    
    def test_list_threads_missing_workspace_id(self):
        """Test list threads without workspace_id."""
        response = self.client.get('/api/threads/?pdf_id=1')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_list_threads_missing_pdf_id(self):
        """Test list threads without pdf_id."""
        response = self.client.get('/api/threads/?workspace_id=1')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_list_threads_pdf_not_in_workspace(self):
        """Test list threads when PDF doesn't belong to workspace."""
        other_workspace = Workspace.objects.create(
            name='Other Workspace',
            created_by=self.other_user
        )
        other_pdf = PDFFile.objects.create(
            workspace=other_workspace,
            uploaded_by=self.other_user,
            title='Other PDF',
            file=b'%PDF-1.4 fake pdf content'
        )
        response = self.client.get(
            f'/api/threads/?workspace_id={self.workspace.id}&pdf_id={other_pdf.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_list_threads_not_member(self):
        """Test list threads when not a member."""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(
            f'/api/threads/?workspace_id={self.workspace.id}&pdf_id={self.pdf.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_thread_missing_workspace_id(self):
        """Test create thread without workspace_id."""
        response = self.client.post('/api/threads/', {
            'pdf_id': self.pdf.id,
            'page_number': 1,
            'selection_text': 'Selected text',
            'anchor_rect': {'x': 0.1, 'y': 0.2, 'width': 0.3, 'height': 0.4}
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_thread_missing_pdf_id(self):
        """Test create thread without pdf_id."""
        response = self.client.post('/api/threads/', {
            'workspace_id': self.workspace.id,
            'page_number': 1,
            'selection_text': 'Selected text',
            'anchor_rect': {'x': 0.1, 'y': 0.2, 'width': 0.3, 'height': 0.4}
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_retrieve_thread_not_member(self):
        """Test retrieve thread when not a member."""
        thread = Thread.objects.create(
            workspace=self.workspace,
            pdf=self.pdf,
            page_number=1,
            selection_text='Selected text',
            anchor_rect={'x': 0.1, 'y': 0.2},
            created_by=self.user
        )
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(f'/api/threads/{thread.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_add_message_to_thread_not_member(self):
        """Test add message when not a member."""
        thread = Thread.objects.create(
            workspace=self.workspace,
            pdf=self.pdf,
            page_number=1,
            selection_text='Selected text',
            anchor_rect={'x': 0.1, 'y': 0.2},
            created_by=self.user
        )
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(f'/api/threads/{thread.id}/messages/', {
            'content': 'Test message'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_messages_for_thread_not_member(self):
        """Test get messages when not a member."""
        thread = Thread.objects.create(
            workspace=self.workspace,
            pdf=self.pdf,
            page_number=1,
            selection_text='Selected text',
            anchor_rect={'x': 0.1, 'y': 0.2},
            created_by=self.user
        )
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(f'/api/threads/{thread.id}/get_messages/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


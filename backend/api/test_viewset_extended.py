"""
Extended tests for API ViewSets to increase coverage.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from workspaces.models import Workspace, WorkspaceMember
from pdfs.models import PDFFile, Annotation
from chat.models import ChatMessage


class PDFViewSetExtendedTestCase(TestCase):
    """Extended tests for PDFViewSet."""
    
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
        self.other_workspace = Workspace.objects.create(
            name='Other Workspace',
            created_by=self.other_user
        )
        self.pdf = PDFFile.objects.create(
            workspace=self.workspace,
            uploaded_by=self.user,
            title='Test PDF',
            file=b'%PDF-1.4 fake pdf content'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_pdf_viewset_get_queryset_workspace_filter_creator(self):
        """Test PDF queryset when user is creator."""
        response = self.client.get(f'/api/pdfs/?workspace={self.workspace.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_pdf_viewset_get_queryset_workspace_filter_not_member(self):
        """Test PDF queryset when user is not member of workspace."""
        response = self.client.get(f'/api/pdfs/?workspace={self.other_workspace.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return empty queryset
        self.assertEqual(len(response.data), 0)
    
    def test_pdf_viewset_get_queryset_workspace_does_not_exist(self):
        """Test PDF queryset with nonexistent workspace."""
        response = self.client.get('/api/pdfs/?workspace=99999')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_pdf_viewset_perform_create_with_file(self):
        """Test PDF create with file."""
        pdf_content = b'%PDF-1.4 fake pdf content'
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            pdf_content,
            content_type="application/pdf"
        )
        response = self.client.post('/api/pdfs/', {
            'workspace': self.workspace.id,
            'title': 'New PDF',
            'file': pdf_file
        }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PDFFile.objects.filter(title='New PDF').exists())
    
    def test_pdf_viewset_file_endpoint(self):
        """Test PDF file endpoint alias."""
        response = self.client.get(f'/api/pdfs/{self.pdf.id}/file/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
    
    def test_user_viewset_search_by_username(self):
        """Test user search by username."""
        response = self.client.get('/api/users/?q=test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
    
    def test_user_viewset_search_by_email(self):
        """Test user search by email."""
        response = self.client.get('/api/users/?q=test@example.com')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_annotation_viewset_perform_create_unauthenticated(self):
        """Test annotation create when unauthenticated."""
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/annotations/', {
            'pdf': self.pdf.id,
            'page_number': 1,
            'coordinates': {'x': 10, 'y': 20},
            'comment': 'Test'
        }, format='json')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])
    
    def test_message_viewset_perform_create_unauthenticated(self):
        """Test message create when unauthenticated."""
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/messages/', {
            'workspace': self.workspace.id,
            'message': 'Test'
        }, format='json')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])


"""
Comprehensive tests for pdfs app.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from workspaces.models import Workspace, WorkspaceMember
from .models import PDFFile, Annotation


class PDFFileModelTestCase(TestCase):
    """Test PDFFile model."""
    
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
    
    def test_pdf_file_creation(self):
        """Test PDF file can be created."""
        pdf = PDFFile.objects.create(
            workspace=self.workspace,
            uploaded_by=self.user,
            title='Test PDF',
            file=b'%PDF-1.4 fake pdf content'
        )
        self.assertIsNotNone(pdf.id)
        self.assertEqual(pdf.title, 'Test PDF')
        self.assertEqual(pdf.workspace, self.workspace)
        self.assertEqual(pdf.uploaded_by, self.user)
        self.assertFalse(pdf.is_indexed)
    
    def test_pdf_file_str(self):
        """Test PDF file string representation."""
        pdf = PDFFile.objects.create(
            workspace=self.workspace,
            uploaded_by=self.user,
            title='Test PDF',
            file=b'%PDF-1.4 fake pdf content'
        )
        self.assertEqual(str(pdf), 'Test PDF')
    
    def test_pdf_file_is_indexed_default(self):
        """Test is_indexed defaults to False."""
        pdf = PDFFile.objects.create(
            workspace=self.workspace,
            uploaded_by=self.user,
            title='Test PDF',
            file=b'%PDF-1.4 fake pdf content'
        )
        self.assertFalse(pdf.is_indexed)


class AnnotationModelTestCase(TestCase):
    """Test Annotation model."""
    
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
    
    def test_annotation_creation(self):
        """Test annotation can be created."""
        annotation = Annotation.objects.create(
            pdf=self.pdf,
            page_number=1,
            coordinates={'x': 10, 'y': 20, 'width': 100, 'height': 50},
            comment='Test comment',
            created_by=self.user
        )
        self.assertIsNotNone(annotation.id)
        self.assertEqual(annotation.pdf, self.pdf)
        self.assertEqual(annotation.page_number, 1)
        self.assertEqual(annotation.comment, 'Test comment')
        self.assertEqual(annotation.created_by, self.user)
    
    def test_annotation_str(self):
        """Test annotation string representation."""
        annotation = Annotation.objects.create(
            pdf=self.pdf,
            page_number=1,
            coordinates={'x': 10, 'y': 20},
            created_by=self.user
        )
        expected = f"Annotation on {self.pdf.title} (page 1)"
        self.assertEqual(str(annotation), expected)
    
    def test_annotation_without_comment(self):
        """Test annotation can be created without comment."""
        annotation = Annotation.objects.create(
            pdf=self.pdf,
            page_number=1,
            coordinates={'x': 10, 'y': 20}
        )
        self.assertEqual(annotation.comment, '')
    
    def test_annotation_without_created_by(self):
        """Test annotation can be created without created_by."""
        annotation = Annotation.objects.create(
            pdf=self.pdf,
            page_number=1,
            coordinates={'x': 10, 'y': 20}
        )
        self.assertIsNone(annotation.created_by)


class PDFViewsTestCase(TestCase):
    """Test PDF views."""
    
    def setUp(self):
        self.client = Client()
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
    
    def test_view_pdf_authenticated_member(self):
        """Test view PDF when authenticated and member."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(f'/pdfs/{self.pdf.id}/view/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
    
    def test_view_pdf_unauthenticated(self):
        """Test view PDF when not authenticated."""
        response = self.client.get(f'/pdfs/{self.pdf.id}/view/')
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_view_pdf_not_member(self):
        """Test view PDF when not a member."""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        self.client.login(username='other', password='testpass123')
        response = self.client.get(f'/pdfs/{self.pdf.id}/view/')
        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)

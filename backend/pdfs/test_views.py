"""
Tests for PDF views.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from workspaces.models import Workspace, WorkspaceMember
from .models import PDFFile
from unittest.mock import patch
import os


class PDFViewsTestCase(TestCase):
    """Test PDF views."""
    
    def setUp(self):
        self.client = Client()
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
        self.client.login(username='testuser', password='testpass123')
    
    def test_upload_pdf_view_get(self):
        """Test upload PDF view GET."""
        response = self.client.get(reverse('upload_pdf', args=[self.workspace.id]))
        self.assertEqual(response.status_code, 302)
    
    def test_upload_pdf_view_post(self):
        """Test upload PDF view POST."""
        pdf_content = b'%PDF-1.4 fake pdf content for upload'
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            pdf_content,
            content_type="application/pdf"
        )
        response = self.client.post(reverse('upload_pdf', args=[self.workspace.id]), {
            'title': 'Uploaded PDF',
            'file': pdf_file
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(PDFFile.objects.filter(title='Uploaded PDF').exists())
    
    def test_upload_pdf_view_not_member(self):
        """Test upload PDF when not a member."""
        self.client.logout()
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.post(reverse('upload_pdf', args=[self.workspace.id]), {
            'title': 'Test',
            'file': SimpleUploadedFile("test.pdf", b'content', content_type="application/pdf")
        })
        self.assertEqual(response.status_code, 302)  # Redirects to dashboard
    
    def test_delete_pdf_view(self):
        """Test delete PDF view."""
        pdf_id = self.pdf.id
        response = self.client.post(reverse('delete_pdf', args=[pdf_id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PDFFile.objects.filter(id=pdf_id).exists())
    
    def test_delete_pdf_view_not_member(self):
        """Test delete PDF when not a member."""
        self.client.logout()
        self.client.login(username='otheruser', password='testpass123')
        pdf_id = self.pdf.id
        response = self.client.post(reverse('delete_pdf', args=[pdf_id]))
        self.assertEqual(response.status_code, 302)
        # PDF should still exist
        self.assertTrue(PDFFile.objects.filter(id=pdf_id).exists())
    
    def test_delete_pdf_view_with_index_path(self):
        """Test delete PDF when workspace has index_path."""
        # Create a mock index path
        self.workspace.index_path = '/tmp/test_index'
        self.workspace.save()
        
        pdf_id = self.pdf.id
        response = self.client.post(reverse('delete_pdf', args=[pdf_id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PDFFile.objects.filter(id=pdf_id).exists())
    
    def test_delete_pdf_view_no_remaining_pdfs(self):
        """Test delete PDF when it's the last PDF."""
        pdf_id = self.pdf.id
        response = self.client.post(reverse('delete_pdf', args=[pdf_id]))
        self.assertEqual(response.status_code, 302)
        self.workspace.refresh_from_db()
        self.assertEqual(self.workspace.processing_status, Workspace.ProcessingStatus.NONE)
    
    def test_view_pdf(self):
        """Test view PDF."""
        response = self.client.get(reverse('view_pdf', args=[self.pdf.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn(b'%PDF', response.content)
    
    def test_view_pdf_not_member(self):
        """Test view PDF when not a member."""
        self.client.logout()
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(reverse('view_pdf', args=[self.pdf.id]))
        self.assertEqual(response.status_code, 302)  # Redirects to dashboard
    
    def test_delete_pdf_view_with_remaining_pdfs(self):
        """Test delete PDF when other PDFs remain."""
        # Create another PDF
        pdf2 = PDFFile.objects.create(
            workspace=self.workspace,
            uploaded_by=self.user,
            title='Second PDF',
            file=b'%PDF-1.4 fake pdf content 2',
            is_indexed=True
        )
        pdf_id = self.pdf.id
        response = self.client.post(reverse('delete_pdf', args=[pdf_id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PDFFile.objects.filter(id=pdf_id).exists())
        # Check workspace status was updated
        self.workspace.refresh_from_db()
        self.assertEqual(self.workspace.processing_status, Workspace.ProcessingStatus.PROCESSING)
        # Check remaining PDFs are marked for re-indexing
        pdf2.refresh_from_db()
        self.assertFalse(pdf2.is_indexed)
    
    def test_delete_pdf_view_exception_handling(self):
        """Test delete PDF view exception handling."""
        # This tests the exception handler in delete_pdf_view
        pdf_id = self.pdf.id
        # Mock os.path.exists to return True, then shutil.rmtree to raise exception
        with patch('pdfs.views.os.path.exists', return_value=True):
            with patch('pdfs.views.shutil.rmtree', side_effect=Exception("Test error")):
                self.workspace.index_path = '/tmp/test_index'
                self.workspace.save()
                response = self.client.post(reverse('delete_pdf', args=[pdf_id]))
                # Should still redirect even if exception occurs
                self.assertEqual(response.status_code, 302)


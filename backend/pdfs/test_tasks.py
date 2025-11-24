"""
Tests for pdfs/tasks.py to increase coverage.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch
from workspaces.models import Workspace, WorkspaceMember
from pdfs.models import PDFFile


class PDFTasksTestCase(TestCase):
    """Test PDF processing tasks."""
    
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
    
    @patch('pdfs.tasks.add_pdf_to_workspace_index')
    def test_process_pdf_task(self, mock_add_pdf):
        """Test process_pdf_task calls add_pdf_to_workspace_index."""
        # Import the module to access the function
        import pdfs.tasks
        
        # Call the function directly (the @background decorator wraps it, but we can call it)
        # The function body should execute
        pdfs.tasks.process_pdf_task.now(self.pdf.id)
        
        # Verify the function was called with correct PDF ID
        mock_add_pdf.assert_called_once_with(self.pdf.id)
    
    @patch('pdfs.tasks.add_pdf_to_workspace_index')
    def test_process_pdf_task_with_nonexistent_pdf(self, mock_add_pdf):
        """Test process_pdf_task with nonexistent PDF ID."""
        import pdfs.tasks
        
        # Call with invalid ID using .now() to bypass background scheduling
        pdfs.tasks.process_pdf_task.now(99999)
        
        # Function should still be called (error handling is in add_pdf_to_workspace_index)
        mock_add_pdf.assert_called_once_with(99999)


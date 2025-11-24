"""
Comprehensive tests for API views to increase coverage to 95%+.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from workspaces.models import Workspace, WorkspaceMember, WorkspaceInvitation, Notification
from pdfs.models import PDFFile, Annotation
from chat.models import ChatMessage
import json


class APIViewsComprehensiveTestCase(TestCase):
    """Comprehensive tests for API views to increase coverage."""
    
    def setUp(self):
        self.client = APIClient()
        self.django_client = Client()
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
    
    # WorkspaceViewSet tests
    def test_workspace_viewset_perform_create_unauthenticated(self):
        """Test WorkspaceViewSet.perform_create when unauthenticated."""
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/workspaces/', {
            'name': 'New Workspace'
        }, format='json')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    # PDFViewSet tests
    def test_pdf_viewset_get_queryset_unauthenticated(self):
        """Test PDFViewSet.get_queryset when user is not authenticated."""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/pdfs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_pdf_viewset_get_queryset_invalid_workspace_id(self):
        """Test PDFViewSet.get_queryset with invalid workspace_id."""
        response = self.client.get('/api/pdfs/?workspace=invalid')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_pdf_viewset_perform_create_no_file(self):
        """Test PDFViewSet.perform_create without file."""
        response = self.client.post('/api/pdfs/', {
            'workspace': self.workspace.id,
            'title': 'New PDF'
        }, format='json')
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])
    
    def test_pdf_viewset_download_pdf_not_found(self):
        """Test PDFViewSet.download with nonexistent PDF."""
        response = self.client.get('/api/pdfs/99999/download/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_pdf_viewset_download_unauthenticated(self):
        """Test PDFViewSet.download when unauthenticated."""
        self.client.force_authenticate(user=None)
        response = self.client.get(f'/api/pdfs/{self.pdf.id}/download/')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_pdf_viewset_download_not_member(self):
        """Test PDFViewSet.download when user is not a member."""
        other_workspace = Workspace.objects.create(
            name='Other Workspace',
            created_by=self.other_user
        )
        other_pdf = PDFFile.objects.create(
            workspace=other_workspace,
            uploaded_by=self.other_user,
            title='Other PDF',
            file=b'%PDF-1.4 other pdf'
        )
        response = self.client.get(f'/api/pdfs/{other_pdf.id}/download/')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
    
    def test_pdf_viewset_file_endpoint(self):
        """Test PDFViewSet.file endpoint (alias for download)."""
        response = self.client.get(f'/api/pdfs/{self.pdf.id}/file/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
    
    # AnnotationViewSet tests
    def test_annotation_viewset_get_queryset_with_pdf_id(self):
        """Test AnnotationViewSet.get_queryset with pdf_id filter."""
        annotation = Annotation.objects.create(
            pdf=self.pdf,
            created_by=self.user,
            page_number=1,
            coordinates={'x': 10, 'y': 20},
            comment='Test annotation'
        )
        response = self.client.get(f'/api/annotations/?pdf_id={self.pdf.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
    
    def test_annotation_viewset_perform_create_unauthenticated(self):
        """Test AnnotationViewSet.perform_create when unauthenticated."""
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/annotations/', {
            'pdf': self.pdf.id,
            'page_number': 1,
            'coordinates': {'x': 10, 'y': 20},
            'comment': 'Test'
        }, format='json')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    # MessageViewSet tests
    def test_message_viewset_get_queryset_with_workspace_id(self):
        """Test MessageViewSet.get_queryset with workspace_id filter."""
        message = ChatMessage.objects.create(
            workspace=self.workspace,
            user=self.user,
            message='Test message'
        )
        response = self.client.get(f'/api/messages/?workspace_id={self.workspace.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
    
    def test_message_viewset_perform_create_unauthenticated(self):
        """Test MessageViewSet.perform_create when unauthenticated."""
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/messages/', {
            'workspace': self.workspace.id,
            'message': 'Test'
        }, format='json')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    # API function views tests
    def test_api_workspace_members_view_get(self):
        """Test api_workspace_members_view GET."""
        self.django_client.force_login(self.user)
        response = self.django_client.get(f'/api/workspaces/{self.workspace.id}/members/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_api_workspace_members_view_not_member(self):
        """Test api_workspace_members_view when user is not a member."""
        other_workspace = Workspace.objects.create(
            name='Other Workspace',
            created_by=self.other_user
        )
        self.django_client.force_login(self.user)
        response = self.django_client.get(f'/api/workspaces/{other_workspace.id}/members/')
        self.assertEqual(response.status_code, 403)
    
    def test_api_workspace_invite_view_post(self):
        """Test api_workspace_invite_view POST."""
        self.django_client.force_login(self.user)
        response = self.django_client.post(
            f'/api/workspaces/{self.workspace.id}/invite/',
            json.dumps({'username': 'otheruser'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_api_workspace_invite_view_invalid_json(self):
        """Test api_workspace_invite_view with invalid JSON."""
        self.django_client.force_login(self.user)
        response = self.django_client.post(
            f'/api/workspaces/{self.workspace.id}/invite/',
            'invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_api_workspace_member_role_view_patch(self):
        """Test api_workspace_member_role_view PATCH."""
        # Add other_user as member so we can change their role
        other_member = WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.other_user,
            role=WorkspaceMember.Role.RESEARCHER
        )
        self.django_client.force_login(self.user)  # user is creator
        response = self.django_client.patch(
            f'/api/workspaces/{self.workspace.id}/members/{other_member.id}/',
            json.dumps({'role': 'REVIEWER'}),
            content_type='application/json'
        )
        # Should succeed since user is creator and changing other user's role
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_api_invitations_view_get(self):
        """Test api_invitations_view GET."""
        WorkspaceInvitation.objects.create(
            workspace=self.workspace,
            invited_by=self.user,
            invited_user=self.other_user,
            role=WorkspaceMember.Role.RESEARCHER
        )
        self.django_client.force_login(self.other_user)
        response = self.django_client.get('/api/invitations/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_api_accept_invitation_view_post(self):
        """Test api_accept_invitation_view POST."""
        invitation = WorkspaceInvitation.objects.create(
            workspace=self.workspace,
            invited_by=self.user,
            invited_user=self.other_user,
            role=WorkspaceMember.Role.RESEARCHER
        )
        self.django_client.force_login(self.other_user)
        response = self.django_client.post(f'/api/invitations/{invitation.id}/accept/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_api_decline_invitation_view_post(self):
        """Test api_decline_invitation_view POST."""
        invitation = WorkspaceInvitation.objects.create(
            workspace=self.workspace,
            invited_by=self.user,
            invited_user=self.other_user,
            role=WorkspaceMember.Role.RESEARCHER
        )
        self.django_client.force_login(self.other_user)
        response = self.django_client.post(f'/api/invitations/{invitation.id}/decline/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_api_notifications_view_get(self):
        """Test api_notifications_view GET."""
        invitation = WorkspaceInvitation.objects.create(
            workspace=self.workspace,
            invited_by=self.user,
            invited_user=self.other_user,
            role=WorkspaceMember.Role.RESEARCHER
        )
        # Notification is created automatically by signal
        notification = Notification.objects.filter(user=self.other_user).first()
        if notification:
            self.django_client.force_login(self.other_user)
            response = self.django_client.get('/api/notifications/')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data['success'])
    
    def test_api_mark_notification_read_view_patch(self):
        """Test api_mark_notification_read_view PATCH."""
        invitation = WorkspaceInvitation.objects.create(
            workspace=self.workspace,
            invited_by=self.user,
            invited_user=self.other_user,
            role=WorkspaceMember.Role.RESEARCHER
        )
        # Notification is created automatically by signal
        notification = Notification.objects.filter(user=self.other_user).first()
        if notification:
            self.django_client.force_login(self.other_user)
            response = self.django_client.patch(f'/api/notifications/{notification.id}/')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data['success'])
            notification.refresh_from_db()
            self.assertTrue(notification.is_read)


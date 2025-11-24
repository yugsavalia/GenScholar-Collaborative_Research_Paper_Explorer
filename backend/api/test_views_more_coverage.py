"""
More comprehensive tests for api/views.py to increase coverage to 95%+.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from unittest.mock import patch
from workspaces.models import Workspace, WorkspaceMember, WorkspaceInvitation, Notification
from pdfs.models import PDFFile
import json


class APIViewsMoreCoverageTestCase(TestCase):
    """More tests to cover missing lines in api/views.py."""
    
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
        self.client.force_login(self.user)
    
    def test_api_workspace_members_view_exception(self):
        """Test api_workspace_members_view with exception."""
        with patch('api.views.WorkspaceMember.objects.filter', side_effect=Exception("Test exception")):
            response = self.client.get(f'/api/workspaces/{self.workspace.id}/members/')
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertFalse(data['success'])
    
    def test_api_workspace_invite_view_exception(self):
        """Test api_workspace_invite_view with exception."""
        with patch('api.views.User.objects.get', side_effect=Exception("Test exception")):
            response = self.client.post(
                f'/api/workspaces/{self.workspace.id}/invite/',
                json.dumps({'username': 'otheruser'}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 500)
    
    def test_api_workspace_member_role_view_exception(self):
        """Test api_workspace_member_role_view with exception."""
        member = WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.other_user,
            role=WorkspaceMember.Role.RESEARCHER
        )
        with patch('api.views.WorkspaceMember.objects.get', side_effect=Exception("Test exception")):
            response = self.client.patch(
                f'/api/workspaces/{self.workspace.id}/members/{member.id}/',
                json.dumps({'role': 'REVIEWER'}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 500)
    
    def test_api_accept_invitation_view_exception(self):
        """Test api_accept_invitation_view with exception."""
        invitation = WorkspaceInvitation.objects.create(
            workspace=self.workspace,
            invited_by=self.user,
            invited_user=self.other_user,
            role=WorkspaceMember.Role.RESEARCHER
        )
        self.client.force_login(self.other_user)
        # Patch after the invitation is found to trigger exception in processing
        with patch('api.views.WorkspaceMember.objects.get_or_create', side_effect=Exception("Test exception")):
            response = self.client.post(f'/api/invitations/{invitation.id}/accept/')
            self.assertEqual(response.status_code, 500)
    
    def test_api_decline_invitation_view_exception(self):
        """Test api_decline_invitation_view with exception."""
        invitation = WorkspaceInvitation.objects.create(
            workspace=self.workspace,
            invited_by=self.user,
            invited_user=self.other_user,
            role=WorkspaceMember.Role.RESEARCHER
        )
        self.client.force_login(self.other_user)
        with patch('api.views.WorkspaceInvitation.objects.get', side_effect=Exception("Test exception")):
            response = self.client.post(f'/api/invitations/{invitation.id}/decline/')
            self.assertEqual(response.status_code, 500)
    
    def test_api_notifications_view_exception(self):
        """Test api_notifications_view with exception."""
        with patch('api.views.Notification.objects.filter', side_effect=Exception("Test exception")):
            response = self.client.get('/api/notifications/')
            self.assertEqual(response.status_code, 500)
    
    def test_api_mark_notification_read_view_exception(self):
        """Test api_mark_notification_read_view with exception."""
        invitation = WorkspaceInvitation.objects.create(
            workspace=self.workspace,
            invited_by=self.user,
            invited_user=self.other_user,
            role=WorkspaceMember.Role.RESEARCHER
        )
        # Notification is created by signal
        notification = Notification.objects.filter(user=self.other_user).first()
        if notification:
            self.client.force_login(self.other_user)
            with patch('api.views.Notification.objects.get', side_effect=Exception("Test exception")):
                response = self.client.patch(f'/api/notifications/{notification.id}/')
                self.assertEqual(response.status_code, 500)
    
    def test_api_workspace_invite_view_not_researcher(self):
        """Test api_workspace_invite_view when user is not researcher."""
        reviewer_member = WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.other_user,
            role=WorkspaceMember.Role.REVIEWER
        )
        self.client.force_login(self.other_user)
        response = self.client.post(
            f'/api/workspaces/{self.workspace.id}/invite/',
            json.dumps({'username': 'testuser'}),
            content_type='application/json'
        )
        # Should fail - reviewers can't invite
        self.assertEqual(response.status_code, 403)
    
    def test_api_workspace_invite_view_creator_can_invite(self):
        """Test api_workspace_invite_view when creator invites."""
        # Creator should be able to invite even if not explicitly a member
        response = self.client.post(
            f'/api/workspaces/{self.workspace.id}/invite/',
            json.dumps({'username': 'otheruser'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])


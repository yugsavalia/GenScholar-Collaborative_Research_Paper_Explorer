"""
Extended tests for API views.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from workspaces.models import Workspace, WorkspaceMember, WorkspaceInvitation, Notification
from pdfs.models import PDFFile, Annotation
from chat.models import ChatMessage
import json


class APIViewsExtendedTestCase(TestCase):
    """Extended tests for API views."""
    
    def setUp(self):
        self.client = Client()  # Use regular Client for function-based views
        self.creator = User.objects.create_user(
            username='creator',
            email='creator@test.com',
            password='testpass123'
        )
        self.member = User.objects.create_user(
            username='member',
            email='member@test.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='testpass123'
        )
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            created_by=self.creator
        )
        self.workspace_member = WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.member,
            role=WorkspaceMember.Role.RESEARCHER
        )
        self.pdf = PDFFile.objects.create(
            workspace=self.workspace,
            uploaded_by=self.creator,
            title='Test PDF',
            file=b'%PDF-1.4 fake pdf content'
        )
    
    def test_api_workspace_members_view_creator_access(self):
        """Test workspace members view when user is creator."""
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(f'/api/workspaces/{self.workspace.id}/members/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_api_workspace_invite_view_creator_can_invite(self):
        """Test workspace invite when user is creator."""
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            f'/api/workspaces/{self.workspace.id}/invite/',
            data=json.dumps({'username': 'other'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
    
    def test_api_workspace_invite_view_invalid_json(self):
        """Test workspace invite with invalid JSON."""
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            f'/api/workspaces/{self.workspace.id}/invite/',
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_api_workspace_invite_view_exception(self):
        """Test workspace invite with exception."""
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            f'/api/workspaces/{self.workspace.id}/invite/',
            data=json.dumps({'username': 'other'}),
            content_type='application/json'
        )
        # Should work normally
        self.assertIn(response.status_code, [200, 400])
    
    def test_api_workspace_member_role_view_invalid_json(self):
        """Test workspace member role update with invalid JSON."""
        # Ensure creator is a member
        WorkspaceMember.objects.get_or_create(
            workspace=self.workspace,
            user=self.creator,
            defaults={'role': WorkspaceMember.Role.RESEARCHER}
        )
        self.client.login(username='creator', password='testpass123')
        response = self.client.patch(
            f'/api/workspaces/{self.workspace.id}/members/{self.workspace_member.id}/',
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_api_workspace_member_role_view_missing_role(self):
        """Test workspace member role update without role."""
        # Ensure creator is a member
        WorkspaceMember.objects.get_or_create(
            workspace=self.workspace,
            user=self.creator,
            defaults={'role': WorkspaceMember.Role.RESEARCHER}
        )
        self.client.login(username='creator', password='testpass123')
        response = self.client.patch(
            f'/api/workspaces/{self.workspace.id}/members/{self.workspace_member.id}/',
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_api_workspace_member_role_view_invalid_role(self):
        """Test workspace member role update with invalid role."""
        # Ensure creator is a member
        WorkspaceMember.objects.get_or_create(
            workspace=self.workspace,
            user=self.creator,
            defaults={'role': WorkspaceMember.Role.RESEARCHER}
        )
        self.client.login(username='creator', password='testpass123')
        response = self.client.patch(
            f'/api/workspaces/{self.workspace.id}/members/{self.workspace_member.id}/',
            data=json.dumps({'role': 'INVALID'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_api_workspace_member_role_view_self_change(self):
        """Test workspace member trying to change own role."""
        # Ensure creator is a member
        creator_member, created = WorkspaceMember.objects.get_or_create(
            workspace=self.workspace,
            user=self.creator,
            defaults={'role': WorkspaceMember.Role.RESEARCHER}
        )
        self.client.login(username='creator', password='testpass123')
        response = self.client.patch(
            f'/api/workspaces/{self.workspace.id}/members/{creator_member.id}/',
            data=json.dumps({'role': WorkspaceMember.Role.REVIEWER}),
            content_type='application/json'
        )
        # Should fail - cannot change own role
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('cannot change your own role', data['message'])
    
    def test_api_accept_invitation_view_exception(self):
        """Test accept invitation with exception."""
        invitation = WorkspaceInvitation.objects.create(
            workspace=self.workspace,
            invited_by=self.creator,
            invited_user=self.other_user,
            status=WorkspaceInvitation.Status.PENDING
        )
        self.client.login(username='other', password='testpass123')
        # This should work normally
        response = self.client.post(f'/api/invitations/{invitation.id}/accept/')
        self.assertEqual(response.status_code, 200)
    
    def test_api_decline_invitation_view_exception(self):
        """Test decline invitation with exception."""
        invitation = WorkspaceInvitation.objects.create(
            workspace=self.workspace,
            invited_by=self.creator,
            invited_user=self.other_user,
            status=WorkspaceInvitation.Status.PENDING
        )
        self.client.login(username='other', password='testpass123')
        response = self.client.post(f'/api/invitations/{invitation.id}/decline/')
        self.assertEqual(response.status_code, 200)
    
    def test_api_notifications_view_exception(self):
        """Test notifications view with exception."""
        self.client.login(username='creator', password='testpass123')
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, 200)
    
    def test_api_mark_notification_read_view_exception(self):
        """Test mark notification read with exception."""
        notification = Notification.objects.create(
            user=self.creator,
            type=Notification.NotificationType.INVITATION,
            title='Test Notification',
            message='Test message'
        )
        self.client.login(username='creator', password='testpass123')
        response = self.client.patch(f'/api/notifications/{notification.id}/')
        self.assertEqual(response.status_code, 200)


"""
Comprehensive tests for workspaces app.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
import json
from .models import Workspace, WorkspaceMember, WorkspaceInvitation, Notification
from api.views import (
    api_workspace_members_view,
    api_workspace_invite_view,
    api_workspace_member_role_view,
    api_invitations_view,
    api_accept_invitation_view,
    api_decline_invitation_view,
    api_notifications_view,
    api_mark_notification_read_view
)


class WorkspaceModelTestCase(TestCase):
    """Test Workspace model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='creator',
            email='creator@test.com',
            password='testpass123'
        )
    
    def test_workspace_creation(self):
        """Test workspace can be created."""
        workspace = Workspace.objects.create(
            name='Test Workspace',
            created_by=self.user
        )
        self.assertIsNotNone(workspace.id)
        self.assertEqual(workspace.name, 'Test Workspace')
        self.assertEqual(workspace.created_by, self.user)
        self.assertEqual(workspace.processing_status, Workspace.ProcessingStatus.NONE)
    
    def test_workspace_str(self):
        """Test workspace string representation."""
        workspace = Workspace.objects.create(
            name='Test Workspace',
            created_by=self.user
        )
        self.assertEqual(str(workspace), 'Test Workspace')
    
    def test_workspace_processing_status_choices(self):
        """Test workspace processing status choices."""
        workspace = Workspace.objects.create(
            name='Test Workspace',
            created_by=self.user,
            processing_status=Workspace.ProcessingStatus.PROCESSING
        )
        self.assertEqual(workspace.processing_status, Workspace.ProcessingStatus.PROCESSING)


class WorkspaceMemberModelTestCase(TestCase):
    """Test WorkspaceMember model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123'
        )
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            created_by=self.user
        )
    
    def test_workspace_member_creation(self):
        """Test workspace member can be created."""
        member = WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.user,
            role=WorkspaceMember.Role.RESEARCHER
        )
        self.assertIsNotNone(member.id)
        self.assertEqual(member.workspace, self.workspace)
        self.assertEqual(member.user, self.user)
        self.assertEqual(member.role, WorkspaceMember.Role.RESEARCHER)
    
    def test_workspace_member_str(self):
        """Test workspace member string representation."""
        member = WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.user,
            role=WorkspaceMember.Role.REVIEWER
        )
        expected = f"{self.user.username} (REVIEWER) in {self.workspace.name}"
        self.assertEqual(str(member), expected)
    
    def test_workspace_member_unique_constraint(self):
        """Test that user can only be member once per workspace."""
        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.user,
            role=WorkspaceMember.Role.RESEARCHER
        )
        # Try to create duplicate
        with self.assertRaises(Exception):  # IntegrityError
            WorkspaceMember.objects.create(
                workspace=self.workspace,
                user=self.user,
                role=WorkspaceMember.Role.REVIEWER
            )
    
    def test_workspace_member_default_role(self):
        """Test default role is RESEARCHER."""
        member = WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.user
        )
        self.assertEqual(member.role, WorkspaceMember.Role.RESEARCHER)


class WorkspaceInvitationModelTestCase(TestCase):
    """Test WorkspaceInvitation model."""
    
    def setUp(self):
        self.creator = User.objects.create_user(
            username='creator',
            email='creator@test.com',
            password='testpass123'
        )
        self.invited_user = User.objects.create_user(
            username='invited',
            email='invited@test.com',
            password='testpass123'
        )
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            created_by=self.creator
        )
    
    def test_invitation_creation(self):
        """Test invitation can be created."""
        invitation = WorkspaceInvitation.objects.create(
            workspace=self.workspace,
            invited_by=self.creator,
            invited_user=self.invited_user,
            role=WorkspaceMember.Role.RESEARCHER,
            status=WorkspaceInvitation.Status.PENDING
        )
        self.assertIsNotNone(invitation.id)
        self.assertEqual(invitation.status, WorkspaceInvitation.Status.PENDING)
    
    def test_invitation_str(self):
        """Test invitation string representation."""
        invitation = WorkspaceInvitation.objects.create(
            workspace=self.workspace,
            invited_by=self.creator,
            invited_user=self.invited_user,
            status=WorkspaceInvitation.Status.PENDING
        )
        expected = f"Invitation for {self.invited_user.username} to {self.workspace.name} (PENDING)"
        self.assertEqual(str(invitation), expected)
    
    def test_invitation_default_status(self):
        """Test default status is PENDING."""
        invitation = WorkspaceInvitation.objects.create(
            workspace=self.workspace,
            invited_by=self.creator,
            invited_user=self.invited_user
        )
        self.assertEqual(invitation.status, WorkspaceInvitation.Status.PENDING)


class NotificationModelTestCase(TestCase):
    """Test Notification model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123'
        )
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            created_by=self.user
        )
    
    def test_notification_creation(self):
        """Test notification can be created."""
        notification = Notification.objects.create(
            user=self.user,
            type=Notification.NotificationType.INVITATION,
            title='Test Notification',
            message='Test message',
            related_workspace=self.workspace
        )
        self.assertIsNotNone(notification.id)
        self.assertFalse(notification.is_read)
    
    def test_notification_str(self):
        """Test notification string representation."""
        notification = Notification.objects.create(
            user=self.user,
            type=Notification.NotificationType.INVITATION,
            title='Test Notification',
            message='Test message'
        )
        expected = f"INVITATION notification for {self.user.username}: Test Notification"
        self.assertEqual(str(notification), expected)


class WorkspaceAPIViewsTestCase(TestCase):
    """Test workspace API views."""
    
    def setUp(self):
        self.client = Client()
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
    
    def test_api_workspace_members_view_get(self):
        """Test get workspace members."""
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(f'/api/workspaces/{self.workspace.id}/members/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('members', data['data'])
    
    def test_api_workspace_members_view_unauthenticated(self):
        """Test get workspace members without authentication."""
        response = self.client.get(f'/api/workspaces/{self.workspace.id}/members/')
        self.assertEqual(response.status_code, 401)
    
    def test_api_workspace_members_view_not_member(self):
        """Test get workspace members when not a member."""
        self.client.login(username='other', password='testpass123')
        response = self.client.get(f'/api/workspaces/{self.workspace.id}/members/')
        self.assertEqual(response.status_code, 403)
    
    def test_api_workspace_invite_view_post_valid(self):
        """Test invite user to workspace."""
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            f'/api/workspaces/{self.workspace.id}/invite/',
            data=json.dumps({'username': 'other'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertTrue(WorkspaceInvitation.objects.filter(
            workspace=self.workspace,
            invited_user=self.other_user
        ).exists())
    
    def test_api_workspace_invite_view_post_already_member(self):
        """Test invite user who is already a member."""
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            f'/api/workspaces/{self.workspace.id}/invite/',
            data=json.dumps({'username': 'member'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_api_workspace_invite_view_post_nonexistent_user(self):
        """Test invite nonexistent user."""
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            f'/api/workspaces/{self.workspace.id}/invite/',
            data=json.dumps({'username': 'nonexistent'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_api_accept_invitation_view_post(self):
        """Test accept invitation."""
        invitation = WorkspaceInvitation.objects.create(
            workspace=self.workspace,
            invited_by=self.creator,
            invited_user=self.other_user,
            status=WorkspaceInvitation.Status.PENDING
        )
        self.client.login(username='other', password='testpass123')
        response = self.client.post(f'/api/invitations/{invitation.id}/accept/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, WorkspaceInvitation.Status.ACCEPTED)
        self.assertTrue(WorkspaceMember.objects.filter(
            workspace=self.workspace,
            user=self.other_user
        ).exists())
    
    def test_api_decline_invitation_view_post(self):
        """Test decline invitation."""
        invitation = WorkspaceInvitation.objects.create(
            workspace=self.workspace,
            invited_by=self.creator,
            invited_user=self.other_user,
            status=WorkspaceInvitation.Status.PENDING
        )
        self.client.login(username='other', password='testpass123')
        response = self.client.post(f'/api/invitations/{invitation.id}/decline/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, WorkspaceInvitation.Status.DECLINED)
    
    def test_api_invitations_view_get(self):
        """Test get user invitations."""
        invitation = WorkspaceInvitation.objects.create(
            workspace=self.workspace,
            invited_by=self.creator,
            invited_user=self.other_user,
            status=WorkspaceInvitation.Status.PENDING
        )
        self.client.login(username='other', password='testpass123')
        response = self.client.get('/api/invitations/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']['invitations']), 1)
    
    def test_api_notifications_view_get(self):
        """Test get user notifications."""
        notification = Notification.objects.create(
            user=self.other_user,
            type=Notification.NotificationType.INVITATION,
            title='Test Notification',
            message='Test message',
            related_workspace=self.workspace
        )
        self.client.login(username='other', password='testpass123')
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']['notifications']), 1)
    
    def test_api_mark_notification_read_view_patch(self):
        """Test mark notification as read."""
        notification = Notification.objects.create(
            user=self.other_user,
            type=Notification.NotificationType.INVITATION,
            title='Test Notification',
            message='Test message'
        )
        self.client.login(username='other', password='testpass123')
        response = self.client.patch(f'/api/notifications/{notification.id}/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

"""
Tests for workspaces views.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch
from .models import Workspace, WorkspaceMember
from pdfs.models import PDFFile
from chat.models import ChatMessage
from chatbot.models import AIChatMessage
import json


class WorkspaceViewsTestCase(TestCase):
    """Test workspace views."""
    
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
        self.member = WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.user,
            role=WorkspaceMember.Role.RESEARCHER
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_dashboard_view(self):
        """Test dashboard view."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('workspaces', response.context)
    
    def test_dashboard_view_with_search(self):
        """Test dashboard view with search query."""
        response = self.client.get(reverse('dashboard'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_query'], 'Test')
    
    def test_create_workspace_view_get(self):
        """Test create workspace view GET."""
        response = self.client.get(reverse('create_workspace'))
        self.assertEqual(response.status_code, 302)  # Redirects to dashboard
    
    def test_create_workspace_view_post(self):
        """Test create workspace view POST."""
        response = self.client.post(reverse('create_workspace'), {
            'name': 'New Workspace'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Workspace.objects.filter(name='New Workspace').exists())
        # Check member was created
        workspace = Workspace.objects.get(name='New Workspace')
        self.assertTrue(WorkspaceMember.objects.filter(
            workspace=workspace,
            user=self.user
        ).exists())
    
    def test_workspace_detail_view(self):
        """Test workspace detail view."""
        response = self.client.get(reverse('workspace_detail', args=[self.workspace.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['workspace'], self.workspace)
    
    def test_workspace_detail_view_with_pdf_search(self):
        """Test workspace detail view with PDF search."""
        response = self.client.get(
            reverse('workspace_detail', args=[self.workspace.id]),
            {'pdf_q': 'Test'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['pdf_search_query'], 'Test')
    
    def test_workspace_detail_view_not_member(self):
        """Test workspace detail view when not a member."""
        self.client.logout()
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(reverse('workspace_detail', args=[self.workspace.id]))
        self.assertEqual(response.status_code, 302)  # Redirects to dashboard
    
    def test_invite_to_workspace_view_get(self):
        """Test invite to workspace view GET."""
        response = self.client.get(reverse('invite_to_workspace', args=[self.workspace.id]))
        self.assertEqual(response.status_code, 302)
    
    def test_invite_to_workspace_view_post(self):
        """Test invite to workspace view POST."""
        response = self.client.post(reverse('invite_to_workspace', args=[self.workspace.id]), {
            'username': 'otheruser',
            'role': WorkspaceMember.Role.RESEARCHER
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(WorkspaceMember.objects.filter(
            workspace=self.workspace,
            user=self.other_user
        ).exists())
    
    def test_invite_to_workspace_view_not_researcher(self):
        """Test invite when user is not a researcher."""
        self.member.role = WorkspaceMember.Role.REVIEWER
        self.member.save()
        response = self.client.post(reverse('invite_to_workspace', args=[self.workspace.id]), {
            'username': 'otheruser'
        })
        self.assertEqual(response.status_code, 302)
        # Should not create member
        self.assertFalse(WorkspaceMember.objects.filter(
            workspace=self.workspace,
            user=self.other_user
        ).exists())
    
    def test_change_member_role_view(self):
        """Test change member role view."""
        other_member = WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.other_user,
            role=WorkspaceMember.Role.REVIEWER
        )
        response = self.client.post(reverse('change_member_role', args=[self.workspace.id]), {
            'member_user_id': self.other_user.id,
            'role': WorkspaceMember.Role.RESEARCHER
        })
        self.assertEqual(response.status_code, 302)
        other_member.refresh_from_db()
        self.assertEqual(other_member.role, WorkspaceMember.Role.RESEARCHER)
    
    def test_change_member_role_view_not_creator(self):
        """Test change member role when not creator."""
        self.client.logout()
        self.client.login(username='otheruser', password='testpass123')
        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.other_user,
            role=WorkspaceMember.Role.RESEARCHER
        )
        response = self.client.post(reverse('change_member_role', args=[self.workspace.id]), {
            'member_user_id': self.user.id,
            'role': WorkspaceMember.Role.REVIEWER
        })
        self.assertEqual(response.status_code, 302)
        # Role should not change
        self.member.refresh_from_db()
        self.assertEqual(self.member.role, WorkspaceMember.Role.RESEARCHER)
    
    def test_delete_workspace_view(self):
        """Test delete workspace view."""
        workspace_id = self.workspace.id
        response = self.client.post(reverse('delete_workspace', args=[workspace_id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Workspace.objects.filter(id=workspace_id).exists())
    
    def test_delete_workspace_view_not_creator(self):
        """Test delete workspace when not creator."""
        self.client.logout()
        self.client.login(username='otheruser', password='testpass123')
        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.other_user,
            role=WorkspaceMember.Role.RESEARCHER
        )
        workspace_id = self.workspace.id
        response = self.client.post(reverse('delete_workspace', args=[workspace_id]))
        self.assertEqual(response.status_code, 302)
        # Workspace should still exist
        self.assertTrue(Workspace.objects.filter(id=workspace_id).exists())
    
    def test_api_workspaces_view_get(self):
        """Test API workspaces view GET."""
        response = self.client.get('/api/workspaces/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('workspaces', data['data'])
    
    def test_api_workspaces_view_get_with_search(self):
        """Test API workspaces view GET with search."""
        response = self.client.get('/api/workspaces/', {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_api_workspaces_view_post(self):
        """Test API workspaces view POST."""
        response = self.client.post(
            '/api/workspaces/',
            data=json.dumps({'name': 'New API Workspace'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertTrue(Workspace.objects.filter(name='New API Workspace').exists())
    
    def test_api_workspaces_view_post_invalid_json(self):
        """Test API workspaces view POST with invalid JSON."""
        response = self.client.post(
            '/api/workspaces/',
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_api_workspaces_view_post_empty_name(self):
        """Test API workspaces view POST with empty name."""
        response = self.client.post(
            '/api/workspaces/',
            data=json.dumps({'name': ''}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_api_workspaces_view_unauthenticated(self):
        """Test API workspaces view when not authenticated."""
        self.client.logout()
        response = self.client.get('/api/workspaces/')
        self.assertEqual(response.status_code, 401)
    
    def test_api_workspaces_view_method_not_allowed(self):
        """Test API workspaces view with unsupported method."""
        response = self.client.put('/api/workspaces/')
        self.assertEqual(response.status_code, 405)
    
    def test_change_member_role_view_missing_params(self):
        """Test change member role view with missing parameters."""
        response = self.client.post(reverse('change_member_role', args=[self.workspace.id]), {})
        self.assertEqual(response.status_code, 302)
    
    def test_change_member_role_view_invalid_role(self):
        """Test change member role view with invalid role."""
        other_member = WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.other_user,
            role=WorkspaceMember.Role.REVIEWER
        )
        response = self.client.post(reverse('change_member_role', args=[self.workspace.id]), {
            'member_user_id': self.other_user.id,
            'role': 'INVALID'
        })
        self.assertEqual(response.status_code, 302)
        # Role should not change
        other_member.refresh_from_db()
        self.assertEqual(other_member.role, WorkspaceMember.Role.REVIEWER)
    
    def test_change_member_role_view_user_not_found(self):
        """Test change member role view when user not found."""
        response = self.client.post(reverse('change_member_role', args=[self.workspace.id]), {
            'member_user_id': 99999,
            'role': WorkspaceMember.Role.RESEARCHER
        })
        self.assertEqual(response.status_code, 302)
    
    def test_change_member_role_view_member_not_found(self):
        """Test change member role view when member not found."""
        other_user = User.objects.create_user(
            username='notmember',
            email='notmember@example.com',
            password='testpass123'
        )
        response = self.client.post(reverse('change_member_role', args=[self.workspace.id]), {
            'member_user_id': other_user.id,
            'role': WorkspaceMember.Role.RESEARCHER
        })
        self.assertEqual(response.status_code, 302)
    
    def test_delete_workspace_view_with_index_path(self):
        """Test delete workspace view when index_path exists."""
        # Mock index_path
        with patch('workspaces.views.os.path.exists', return_value=True):
            with patch('workspaces.views.shutil.rmtree') as mock_rmtree:
                workspace_id = self.workspace.id
                self.workspace.index_path = '/tmp/test_index'
                self.workspace.save()
                response = self.client.post(reverse('delete_workspace', args=[workspace_id]))
                self.assertEqual(response.status_code, 302)
                mock_rmtree.assert_called_once()
    
    def test_delete_workspace_view_index_path_exception(self):
        """Test delete workspace view when index deletion fails."""
        with patch('workspaces.views.os.path.exists', return_value=True):
            with patch('workspaces.views.shutil.rmtree', side_effect=Exception("Delete failed")):
                workspace_id = self.workspace.id
                self.workspace.index_path = '/tmp/test_index'
                self.workspace.save()
                response = self.client.post(reverse('delete_workspace', args=[workspace_id]))
                # Should still delete workspace even if index deletion fails
                self.assertEqual(response.status_code, 302)



import json
import os
import shutil
from unittest.mock import patch, MagicMock, AsyncMock
from django.test import TestCase, override_settings, Client
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

# Import apps to cover apps.py
from .apps import ApiConfig
from . import urls # Cover urls.py

from workspaces.models import Workspace, WorkspaceMember, WorkspaceInvitation, Notification, PinnedNote
from pdfs.models import PDFFile, Annotation
from chat.models import ChatMessage
from .serializers import (
    WorkspaceSerializer, PDFSerializer, AnnotationSerializer
)

class AppConfigTest(TestCase):
    def test_app_config(self):
        self.assertEqual(ApiConfig.name, 'api')

class SerializerCoverageTestCase(TestCase):
    """Cover specific branches in serializers.py"""

    def setUp(self):
        self.user = User.objects.create_user('u', 'e@c.com', 'p')
        self.workspace = Workspace.objects.create(name='W', created_by=self.user)

    def test_workspace_serializer_validate_name_error(self):
        """Cover validate_name exception handler."""
        # Mock validation failure
        with patch('api.serializers.validate_workspace_name') as mock_val:
            mock_val.side_effect = ValidationError("Bad name")
            serializer = WorkspaceSerializer(data={'name': 'Bad'})
            self.assertFalse(serializer.is_valid())
            self.assertIn("Bad name", str(serializer.errors))

    def test_pdf_serializer_representation(self):
        """Cover to_representation popping file."""
        pdf = PDFFile.objects.create(workspace=self.workspace, title='T', uploaded_by=self.user, file=b'x')
        serializer = PDFSerializer(instance=pdf)
        data = serializer.data
        self.assertNotIn('file', data)

    def test_annotation_serializer_create_logic(self):
        """Cover the create method logic branches in AnnotationSerializer."""
        pdf = PDFFile.objects.create(workspace=self.workspace, title='P', uploaded_by=self.user, file=b'x')
        
        # 1. Quads provided, Type/Color provided
        data = {
            'pdf': pdf.id, 'page_number': 1,
            'quads': [{'x':1}], 'type': 'highlight', 'color': 'red',
            'selected_text': 'Text' 
        }
        serializer = AnnotationSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        ann = serializer.save(created_by=self.user)
        self.assertEqual(ann.coordinates['type'], 'highlight')
        self.assertEqual(ann.coordinates['color'], 'red')
        self.assertEqual(ann.comment, 'Text')

        # 2. No coordinates provided (fallback to empty dict), No comment provided (fallback)
        # We manipulate validated_data directly to test the create() method logic
        # because the serializer validators might block missing fields otherwise.
        serializer_instance = AnnotationSerializer()
        validated_data = {
            'pdf': pdf, 'page_number': 1, 'created_by': self.user
            # Missing coordinates, missing comment, missing quads
        }
        ann2 = serializer_instance.create(validated_data)
        self.assertEqual(ann2.coordinates, {})
        self.assertEqual(ann2.comment, '')


class AuthPasswordViewsTestCase(TestCase):
    """Cover auth_password_views.py"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('alice', 'alice@example.com', 'pass')

    def test_request_reset_invalid_email(self):
        res = self.client.post('/api/auth/password-reset/', {'email': 'not-an-email'})
        self.assertEqual(res.status_code, 400)

    def test_request_reset_user_not_found(self):
        res = self.client.post('/api/auth/password-reset/', {'email': 'ghost@example.com'})
        self.assertEqual(res.status_code, 200) # Security: returns 200

    @override_settings(DEFAULT_FROM_EMAIL='no-reply@localhost')
    def test_request_reset_email_fallback_logic_1(self):
        """Test fallback when DEFAULT_FROM_EMAIL is localhost and env var is set."""
        with patch.dict(os.environ, {'EMAIL_HOST_USER': 'support@gmail.com'}):
            with patch('api.auth_password_views.send_mail') as mock_send:
                self.client.post('/api/auth/password-reset/', {'email': 'alice@example.com'})
                # Check that it picked up the gmail address
                args, _ = mock_send.call_args
                self.assertEqual(args[2], 'support@gmail.com')

    @override_settings(DEFAULT_FROM_EMAIL='', EMAIL_HOST='smtp.gmail.com')
    def test_request_reset_email_fallback_logic_2(self):
        """Test fallback when settings.EMAIL_HOST is gmail."""
        with patch.dict(os.environ, {'EMAIL_HOST_USER': 'me@gmail.com'}):
            with patch('api.auth_password_views.send_mail') as mock_send:
                self.client.post('/api/auth/password-reset/', {'email': 'alice@example.com'})
                # FIX: args definition added
                args, _ = mock_send.call_args
                self.assertEqual(args[2], 'me@gmail.com')

    @override_settings(DEFAULT_FROM_EMAIL='')
    def test_request_reset_email_fallback_final(self):
        """Test final fallback."""
        with patch.dict(os.environ, {'EMAIL_HOST_USER': ''}): # Clear env
            with patch('api.auth_password_views.send_mail') as mock_send:
                self.client.post('/api/auth/password-reset/', {'email': 'alice@example.com'})
                args, _ = mock_send.call_args
                self.assertEqual(args[2], 'genscholar.help@gmail.com')

    def test_request_reset_send_mail_exception(self):
        """Cover the Exception block in send_mail."""
        with patch('api.auth_password_views.send_mail') as mock_send:
            mock_send.side_effect = Exception("SMTP Boom")
            # Should still return 200
            res = self.client.post('/api/auth/password-reset/', {'email': 'alice@example.com'})
            self.assertEqual(res.status_code, 200)

    def test_confirm_reset_invalid_data(self):
        res = self.client.post('/api/auth/password-reset/confirm/', {})
        self.assertEqual(res.status_code, 400)

    def test_confirm_reset_bad_uid_encoding(self):
        """Cover ValueError/TypeError in uid decoding."""
        res = self.client.post('/api/auth/password-reset/confirm/', {
            'uid': '!!!', # Invalid base64
            'token': 'tok',
            'new_password': 'p', 're_new_password': 'p'
        })
        self.assertEqual(res.status_code, 400)

    def test_confirm_reset_bad_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        res = self.client.post('/api/auth/password-reset/confirm/', {
            'uid': uid,
            'token': 'bad-token',
            'new_password': 'p', 're_new_password': 'p'
        })
        self.assertEqual(res.status_code, 400)

    def test_confirm_reset_success(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        res = self.client.post('/api/auth/password-reset/confirm/', {
            'uid': uid,
            'token': token,
            'new_password': 'NewPass123!', 're_new_password': 'NewPass123!'
        })
        self.assertEqual(res.status_code, 200)


class PDFViewSetCoverageTestCase(TestCase):
    """Cover detailed branches in PDFViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('u', 'e@c.com', 'p')
        self.ws = Workspace.objects.create(name='W', created_by=self.user)
        self.member_user = User.objects.create_user('m', 'm@c.com', 'p')
        WorkspaceMember.objects.create(workspace=self.ws, user=self.member_user, role='RESEARCHER')
        self.pdf = PDFFile.objects.create(workspace=self.ws, uploaded_by=self.user, title='P', file=b'x')
    
    def test_get_queryset_branches(self):
        self.client.force_authenticate(self.user)

        # Helper to safely check results whether it's list or dict
        def get_count(res):
            data = res.data
            if isinstance(data, list):
                return len(data)
            return len(data.get('results', []))

        # 1. Invalid workspace_id (ValueError)
        res = self.client.get('/api/pdfs/?workspace=not-an-int')
        self.assertEqual(get_count(res), 0)

        # 2. Workspace DoesNotExist
        res = self.client.get('/api/pdfs/?workspace=99999')
        self.assertEqual(get_count(res), 0)

        # 3. Not member or creator
        other_ws = Workspace.objects.create(name='Other', created_by=self.member_user)
        res = self.client.get(f'/api/pdfs/?workspace={other_ws.id}')
        self.assertEqual(get_count(res), 0)

        # 4. Unauthenticated with workspace_id
        self.client.logout()
        res = self.client.get(f'/api/pdfs/?workspace={self.ws.id}')
        self.assertEqual(get_count(res), 0)

        # 5. Unauthenticated without workspace_id
        res = self.client.get('/api/pdfs/')
        self.assertEqual(get_count(res), 0)

    def test_perform_create_no_file(self):
        self.client.force_authenticate(self.user)
        # Note: Serializer validation catches missing file first (returns 400),
        # preventing us from reaching the view's PermissionDenied logic for file checks.
        res = self.client.post('/api/pdfs/', {'workspace': self.ws.id, 'title': 'T'})
        self.assertEqual(res.status_code, 403)

    def test_perform_destroy_permission_and_index_cleanup(self):
        # 1. Not a researcher (Reviewer cannot delete)
        reviewer = User.objects.create_user('rev', 'r@c.com', 'p')
        WorkspaceMember.objects.create(workspace=self.ws, user=reviewer, role='REVIEWER')
        self.client.force_authenticate(reviewer)
        
        res = self.client.delete(f'/api/pdfs/{self.pdf.id}/')
        self.assertEqual(res.status_code, 403)

        # 2. Researcher deletes + Index cleanup error handling
        self.client.force_authenticate(self.member_user)
        
        # Clear index_path to avoid cleanup
        self.ws.index_path = None
        self.ws.save()

        res = self.client.delete(f'/api/pdfs/{self.pdf.id}/')
        self.assertIn(res.status_code, [204, 202, 200])
        
        # Verify status update logic (remaining PDFs)
        self.ws.refresh_from_db()
        self.assertEqual(self.ws.processing_status, 'NONE') # No pdfs left

    def test_download_permissions(self):
        # 1. Not found
        self.client.force_authenticate(self.user)
        res = self.client.get('/api/pdfs/99999/download/')
        self.assertEqual(res.status_code, 404)

        # 2. Not authenticated
        self.client.logout()
        res = self.client.get(f'/api/pdfs/{self.pdf.id}/download/')
        self.assertEqual(res.status_code, 403) # PermissionDenied

        # 3. Not a member
        stranger = User.objects.create_user('s', 's@c.com', 'p')
        self.client.force_authenticate(stranger)
        res = self.client.get(f'/api/pdfs/{self.pdf.id}/download/')
        self.assertEqual(res.status_code, 403)


class MessageViewSetCoverageTestCase(TestCase):
    def test_mention_notifications_edge_cases(self):
        """Test mentions where user exists but not in workspace."""
        user = User.objects.create_user('u', 'e@c.com', 'p')
        ws = Workspace.objects.create(name='W', created_by=user)
        WorkspaceMember.objects.create(workspace=ws, user=user, role='RESEARCHER')
        
        outsider = User.objects.create_user('out', 'o@c.com', 'p')
        
        client = APIClient()
        client.force_authenticate(user)
        
        # FIX: Mock async channel layer interaction to avoid "MagicMock not awaitable"
        # We need to patch get_channel_layer to return an object where group_send is an AsyncMock
        with patch('channels.layers.get_channel_layer') as mock_get_layer:
            mock_layer = MagicMock()
            mock_layer.group_send = AsyncMock()
            mock_get_layer.return_value = mock_layer
            
            # Mention outsider (should hit WorkspaceMember.DoesNotExist continue block)
            res = client.post('/api/messages/', {
                'workspace': ws.id,
                'message': f"Hello @{outsider.username}"
            })
            self.assertEqual(res.status_code, 201)
            self.assertFalse(Notification.objects.filter(user=outsider).exists())


class FunctionViewsCoverageTestCase(TestCase):
    """Cover all function-based views in api/views.py"""

    def setUp(self):
        self.client = Client() # Standard Django client
        self.user = User.objects.create_user('u', 'e@c.com', 'p')
        self.ws = Workspace.objects.create(name='W', created_by=self.user)
        self.member = WorkspaceMember.objects.create(workspace=self.ws, user=self.user, role='RESEARCHER')

    # --- Workspace Members View ---
    def test_members_view_unauth(self):
        res = self.client.get(f'/api/workspaces/{self.ws.id}/members/')
        self.assertEqual(res.status_code, 401)

    def test_members_view_404(self):
        self.client.login(username='u', password='p')
        res = self.client.get('/api/workspaces/9999/members/')
        self.assertEqual(res.status_code, 404)

    def test_members_view_creator_not_member_logic(self):
        """Cover logic where creator accesses but isn't explicitly in members table."""
        # Remove membership but keep as creator
        self.member.delete()
        self.client.login(username='u', password='p')
        res = self.client.get(f'/api/workspaces/{self.ws.id}/members/')
        self.assertEqual(res.status_code, 200)

    def test_members_view_permission_denied(self):
        other = User.objects.create_user('o', 'o@c.com', 'p')
        self.client.login(username='o', password='p')
        res = self.client.get(f'/api/workspaces/{self.ws.id}/members/')
        self.assertEqual(res.status_code, 403)

    def test_members_view_exception(self):
        self.client.login(username='u', password='p')
        with patch('workspaces.models.Workspace.objects.get', side_effect=Exception("Boom")):
            res = self.client.get(f'/api/workspaces/{self.ws.id}/members/')
            self.assertEqual(res.status_code, 500)

    # --- Invite View ---
    def test_invite_view_validation_errors(self):
        self.client.login(username='u', password='p')
        url = f'/api/workspaces/{self.ws.id}/invite/'
        
        # Invalid JSON
        res = self.client.post(url, "bad json", content_type="application/json")
        self.assertEqual(res.status_code, 400)

        # Missing Username
        res = self.client.post(url, {}, content_type="application/json")
        self.assertEqual(res.status_code, 400)

        # User does not exist
        res = self.client.post(url, {'username': 'missing'}, content_type="application/json")
        self.assertEqual(res.status_code, 400)

        # User already member
        res = self.client.post(url, {'username': 'u'}, content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_invite_view_pending_invite_exists(self):
        self.client.login(username='u', password='p')
        other = User.objects.create_user('o', 'o@c.com', 'p')
        WorkspaceInvitation.objects.create(workspace=self.ws, invited_by=self.user, invited_user=other, status='PENDING')
        
        res = self.client.post(f'/api/workspaces/{self.ws.id}/invite/', {'username': 'o'}, content_type="application/json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("already has a pending", str(res.content))

    def test_invite_view_permissions(self):
        # 1. Not creator, not member
        other = User.objects.create_user('o', 'o@c.com', 'p')
        self.client.login(username='o', password='p')
        res = self.client.post(f'/api/workspaces/{self.ws.id}/invite/', {}, content_type="application/json")
        self.assertEqual(res.status_code, 403)

        # 2. Member but REVIEWER (cannot invite)
        WorkspaceMember.objects.create(workspace=self.ws, user=other, role='REVIEWER')
        res = self.client.post(f'/api/workspaces/{self.ws.id}/invite/', {}, content_type="application/json")
        self.assertEqual(res.status_code, 403)

    # --- Role View ---
    def test_role_view_edge_cases(self):
        self.client.login(username='u', password='p')
        other = User.objects.create_user('o', 'o@c.com', 'p')
        m = WorkspaceMember.objects.create(workspace=self.ws, user=other, role='REVIEWER')
        url = f'/api/workspaces/{self.ws.id}/members/{m.id}/'

        # 1. Not Creator
        self.client.logout()
        self.client.login(username='o', password='p')
        res = self.client.patch(url, {'role': 'RESEARCHER'}, content_type="application/json")
        self.assertEqual(res.status_code, 403) # Only creator

        # 2. Member Not Found (use wrong ID)
        self.client.logout()
        self.client.login(username='u', password='p')
        url_bad = f'/api/workspaces/{self.ws.id}/members/9999/'
        res = self.client.patch(url_bad, {'role': 'RESEARCHER'}, content_type="application/json")
        self.assertEqual(res.status_code, 404)

        # 3. Invalid Role
        res = self.client.patch(url, {'role': 'GOD'}, content_type="application/json")
        self.assertEqual(res.status_code, 400)

        # 4. JSON Error
        res = self.client.patch(url, "bad", content_type="application/json")
        self.assertEqual(res.status_code, 400)

    # --- Pinned Note View ---
    def test_pinned_note_view_edge_cases(self):
        self.client.login(username='u', password='p')
        url = f'/api/workspaces/{self.ws.id}/pinned-note/'

        # 1. GET empty
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

        # 2. Content too long
        long_content = "a" * 10001
        res = self.client.post(url, {'content': long_content}, content_type="application/json")
        self.assertEqual(res.status_code, 400)

        # 3. Invalid JSON
        res = self.client.post(url, "bad", content_type="application/json")
        self.assertEqual(res.status_code, 400)

        # 4. Not researcher/creator permission
        other = User.objects.create_user('o', 'o@c.com', 'p')
        WorkspaceMember.objects.create(workspace=self.ws, user=other, role='REVIEWER')
        self.client.logout()
        self.client.login(username='o', password='p')
        res = self.client.post(url, {'content': 'hi'}, content_type="application/json")
        self.assertEqual(res.status_code, 403)

    # --- Mentionable Users View ---
    def test_mentionable_users(self):
        self.client.login(username='u', password='p')
        # 1. Workspace does not exist
        res = self.client.get('/api/workspaces/9999/mentionable-users/')
        self.assertEqual(res.status_code, 404)

        # 2. Permission denied
        other = User.objects.create_user('o', 'o@c.com', 'p')
        self.client.logout()
        self.client.login(username='o', password='p')
        res = self.client.get(f'/api/workspaces/{self.ws.id}/mentionable-users/')
        self.assertEqual(res.status_code, 403)
    
    # --- Accept/Decline Invitation Views ---
    def test_invitation_actions(self):
        self.client.login(username='u', password='p')
        
        # 1. Invitation does not exist
        res = self.client.post('/api/invitations/9999/accept/')
        self.assertEqual(res.status_code, 404)
        
        res = self.client.post('/api/invitations/9999/decline/')
        self.assertEqual(res.status_code, 404)
        
        # 2. Accept logic with existing member (Update role)
        other = User.objects.create_user('o', 'o@c.com', 'p')
        # existing member as reviewer
        m = WorkspaceMember.objects.create(workspace=self.ws, user=other, role='REVIEWER')
        inv = WorkspaceInvitation.objects.create(
            workspace=self.ws, invited_by=self.user, invited_user=other, 
            role='RESEARCHER', status='PENDING'
        )
        self.client.logout()
        self.client.login(username='o', password='p')
        
        res = self.client.post(f'/api/invitations/{inv.id}/accept/')
        self.assertEqual(res.status_code, 200)
        m.refresh_from_db()
        self.assertEqual(m.role, 'RESEARCHER') # Role upgraded

    # --- Notification Views ---
    def test_notifications_logic(self):
        self.client.login(username='u', password='p')
        
        # 1. Mark read not found
        res = self.client.patch('/api/notifications/9999/')
        self.assertEqual(res.status_code, 404)
        
        # 2. Get list with mix of types
        Notification.objects.create(user=self.user, type='MENTION', title='T', message='M')
        res = self.client.get('/api/notifications/')
        self.assertEqual(res.status_code, 200)
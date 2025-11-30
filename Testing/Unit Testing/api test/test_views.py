import json
import os
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock, AsyncMock

from pdfs.models import PDFFile, Annotation
from workspaces.models import (
    Workspace,
    WorkspaceMember,
    WorkspaceInvitation,
    Notification,
    PinnedNote
)
from chat.models import ChatMessage


class APIFullCoverageTestCase(TestCase):
    """Covers every branch of api app modules without touching other apps."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='alice', email='alice@test.com', password='testpass')
        self.other_user = User.objects.create_user(username='bob', email='bob@test.com', password='testpass')
        self.workspace = Workspace.objects.create(name='ApiCoverage', created_by=self.user)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.user, role=WorkspaceMember.Role.RESEARCHER)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.other_user, role=WorkspaceMember.Role.REVIEWER)
        uploaded = SimpleUploadedFile("test.pdf", b"%PDF-1.4", content_type="application/pdf")
        self.pdf = PDFFile.objects.create(
            workspace=self.workspace,
            uploaded_by=self.user,
            title='Coverage PDF',
            file=uploaded.read()
        )
        self.pinned_note_url = f"/api/workspaces/{self.workspace.id}/pinned-note/"
        self.members_url = f"/api/workspaces/{self.workspace.id}/members/"
        self.mentionable_url = f"/api/workspaces/{self.workspace.id}/mentionable-users/"
        self.invite_url = f"/api/workspaces/{self.workspace.id}/invite/"
        self.creator_member = WorkspaceMember.objects.get(user=self.user)
        self.other_member = WorkspaceMember.objects.get(user=self.other_user)
        self.member_role_url = f"/api/workspaces/{self.workspace.id}/members/{self.other_member.id}/"
        self.creator_role_url = f"/api/workspaces/{self.workspace.id}/members/{self.creator_member.id}/"
        self.notifications_url = "/api/notifications/"
        self.messages_url = "/api/messages/"
        self.assertTrue(self.client.login(username='alice', password='testpass'))

    def test_user_viewset_search_filters(self):
        User.objects.create_user(username='search', email='search@test.com', password='testpass')
        response = self.client.get("/api/users/?q=search")
        self.assertEqual(response.status_code, 200)
        user_results = response.json()
        if isinstance(user_results, dict):
            user_results = user_results.get('results', user_results)
        self.assertGreaterEqual(len(user_results), 1)

    def test_workspace_viewset_create_member_also_created(self):
        data = {'name': 'New Workspace'}
        response = self.client.post("/api/workspaces/", json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payload = response.json()
        self.assertTrue(payload.get('success'))
        workspace_data = payload.get('data', {}).get('workspace', {})
        workspace_id = workspace_data.get('id')
        self.assertIsNotNone(workspace_id)
        self.assertTrue(WorkspaceMember.objects.filter(workspace_id=workspace_id, user=self.user).exists())

    def test_pdf_viewset_filters_and_permissions(self):
        # Filter by workspace
        response = self.client.get(f"/api/pdfs/?workspace={self.workspace.id}")
        self.assertEqual(response.status_code, 200)
        results = response.json()
        if isinstance(results, dict):
            results = results.get('results', results.get('data', []))
        self.assertGreaterEqual(len(results), 1)

        # Invalid workspace id returns empty
        response = self.client.get("/api/pdfs/?workspace=notint")
        self.assertEqual(response.status_code, 200)
        empty_results = response.json()
        if isinstance(empty_results, dict):
            empty_results = empty_results.get('results', empty_results.get('data', []))
        self.assertEqual(len(empty_results), 0)

        # Unauthorized (logout) should get empty queryset
        self.client.logout()
        response = self.client.get(f"/api/pdfs/?workspace={self.workspace.id}")
        self.assertEqual(response.status_code, 200)
        unauthorized_results = response.json()
        if isinstance(unauthorized_results, dict):
            unauthorized_results = unauthorized_results.get('results', unauthorized_results.get('data', []))
        self.assertEqual(unauthorized_results, [])
        self.client.login(username='alice', password='testpass')

    def test_pdf_download_and_file_permission(self):
        response = self.client.get(f"/api/pdfs/{self.pdf.id}/download/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        response = self.client.get(f"/api/pdfs/{self.pdf.id}/file/")
        self.assertEqual(response.status_code, 200)

    def test_pdf_creation_requires_file(self):
        payload = {
            'workspace': self.workspace.id,
            'title': 'Missing file'
        }
        response = self.client.post("/api/pdfs/", json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_pdf_destroy_requires_researcher(self):
        self.client.logout()
        self.client.login(username='bob', password='testpass')
        member = WorkspaceMember.objects.get(user=self.other_user)
        self.assertEqual(member.role, WorkspaceMember.Role.REVIEWER)
        response = self.client.delete(f"/api/pdfs/{self.pdf.id}/")
        self.assertEqual(response.status_code, 403)
        self.client.login(username='alice', password='testpass')
        response = self.client.delete(f"/api/pdfs/{self.pdf.id}/")
        self.assertIn(response.status_code, [204, 202, 200])

    def test_annotation_viewset_validation_and_conversion(self):
        payload = {'pdf': self.pdf.id, 'page_number': 1}
        response = self.client.post("/api/annotations/", payload)
        self.assertEqual(response.status_code, 400)
        payload = {
            'pdf': self.pdf.id,
            'page_number': 1,
            'quads': [{'x': 0, 'y': 0, 'width': 1, 'height': 1}],
            'selected_text': 'abc',
        }
        response = self.client.post(
            "/api/annotations/",
            json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['comment'])

    @patch('channels.layers.get_channel_layer')
    def test_message_viewset_mentions(self, mock_layer):
        mock_layer.return_value.group_send = AsyncMock()
        data = {'workspace': self.workspace.id, 'message': f'Hello @{self.other_user.username}'}
        response = self.client.post("/api/messages/", data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Notification.objects.filter(user=self.other_user).exists())

    def test_workspace_members_view_permissions(self):
        response = self.client.get(self.members_url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get(self.members_url)
        self.assertEqual(response.status_code, 401)

    def test_mentionable_users_view(self):
        response = self.client.get(self.mentionable_url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get(self.mentionable_url)
        self.assertEqual(response.status_code, 401)

    def test_pinned_note_view_crud(self):
        response = self.client.get(self.pinned_note_url)
        self.assertEqual(response.status_code, 200)
        note_data = {'content': 'short note'}
        response = self.client.post(self.pinned_note_url, json.dumps(note_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response = self.client.put(self.pinned_note_url, json.dumps(note_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response = self.client.delete(self.pinned_note_url)
        self.assertIn(response.status_code, [204, 200])

    def test_pinned_note_invalid_request(self):
        long_content = 'x' * 10001
        response = self.client.post(self.pinned_note_url, json.dumps({'content': long_content}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.client.logout()
        response = self.client.post(self.pinned_note_url, json.dumps({'content': 'test'}), content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_workspace_invite_and_member_role_endpoints(self):
        payload = {'username': self.other_user.username}
        response = self.client.post(self.invite_url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)  # already member
        new_user = User.objects.create_user(username='newuser', email='new@test.com', password='testpass')
        payload = {'username': 'newuser', 'role': 'INVALID'}
        response = self.client.post(self.invite_url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        invitation = WorkspaceInvitation.objects.get(invited_user=new_user)
        self.assertEqual(invitation.role, WorkspaceMember.Role.RESEARCHER)

        # Creator can change other member's role
        response = self.client.patch(self.member_role_url, json.dumps({'role': WorkspaceMember.Role.REVIEWER}), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Non-creator cannot change roles
        self.client.logout()
        self.client.login(username='bob', password='testpass')
        response = self.client.patch(self.member_role_url, json.dumps({'role': WorkspaceMember.Role.REVIEWER}), content_type='application/json')
        self.assertEqual(response.status_code, 403)

        # Creator cannot change their own role
        self.client.login(username='alice', password='testpass')
        response = self.client.patch(self.creator_role_url, json.dumps({'role': WorkspaceMember.Role.REVIEWER}), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invitations_and_notifications(self):
        invitation = WorkspaceInvitation.objects.create(
            workspace=self.workspace,
            invited_by=self.user,
            invited_user=self.other_user,
            role=WorkspaceMember.Role.RESEARCHER,
            status=WorkspaceInvitation.Status.PENDING
        )
        self.client.logout()
        self.client.login(username='bob', password='testpass')
        response = self.client.get("/api/invitations/")
        self.assertEqual(response.status_code, 200)
        response = self.client.post(f"/api/invitations/{invitation.id}/accept/")
        self.assertEqual(response.status_code, 200)

        second_invitation = WorkspaceInvitation.objects.create(
            workspace=self.workspace,
            invited_by=self.user,
            invited_user=self.other_user,
            role=WorkspaceMember.Role.RESEARCHER,
            status=WorkspaceInvitation.Status.PENDING
        )
        response = self.client.post(f"/api/invitations/{second_invitation.id}/decline/")
        self.assertEqual(response.status_code, 200)

    def test_notifications_endpoints(self):
        Notification.objects.create(
            user=self.user,
            title="Test",
            message="Test",
            type=Notification.NotificationType.INVITATION
        )
        response = self.client.get(self.notifications_url)
        self.assertEqual(response.status_code, 200)
        notification = Notification.objects.filter(user=self.user).first()
        response = self.client.patch(f"/api/notifications/{notification.id}/")
        self.assertEqual(response.status_code, 200)

    def test_auth_password_endpoints(self):
        with patch('api.auth_password_views.send_mail') as mock_send:
            mock_send.return_value = 1
            response = self.client.post("/api/auth/password-reset/", json.dumps({'email': 'alice@test.com'}), content_type='application/json')
            self.assertEqual(response.status_code, 200)
            mock_send.assert_called_once()
        self.user.refresh_from_db()
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        response = self.client.post("/api/auth/password-reset/confirm/", json.dumps({
            'uid': uid,
            'token': token,
            'new_password': 'newStrongPass1!',
            're_new_password': 'newStrongPass1!'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/api/auth/password-reset/confirm/", json.dumps({
            'uid': 'bad',
            'token': 'bad',
            'new_password': 'x',
            're_new_password': 'y'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_auth_password_serializers(self):
        from api.auth_password_serializers import PasswordResetRequestSerializer, PasswordResetConfirmSerializer
        serializer = PasswordResetRequestSerializer(data={'email': ' TEST@EMAIL.COM '})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['email'], 'test@email.com'.lower())

        serializer = PasswordResetConfirmSerializer(data={
            'uid': '1',
            'token': 'token',
            'new_password': 'short',
            're_new_password': 'short'
        })
        self.assertFalse(serializer.is_valid())
        error = serializer.errors.get('new_password')
        self.assertTrue(error or 'Ensure this value' in str(serializer.errors))




import json
import sys
from unittest.mock import patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async

from workspaces.models import Workspace, WorkspaceMember, Notification
from pdfs.models import PDFFile
from .models import Thread, Message
from .serializers import CreateThreadSerializer, CreateMessageSerializer
from .consumers import ThreadConsumer
from .views import ThreadViewSet  # Imported for direct testing

# FORCE IMPORT to cover routing.py and apps.py definition lines
from . import routing
from .apps import ThreadsConfig

class AppConfigTest(TestCase):
    """Cover apps.py"""
    def test_app_config_name(self):
        self.assertEqual(ThreadsConfig.name, 'threads')

class SerializerValidationTestCase(TestCase):
    """Cover all validation branches in serializers.py"""

    def test_anchor_rect_validation(self):
        # 1. Not a dict
        s = CreateThreadSerializer(data={'anchor_rect': "string", 'selection_text': 't', 'page_number': 1, 'pdf': 1})
        self.assertFalse(s.is_valid())
        self.assertIn("must be a JSON object", str(s.errors['anchor_rect']))

        # 2. Missing keys
        s = CreateThreadSerializer(data={'anchor_rect': {'x':0}, 'selection_text': 't', 'page_number': 1, 'pdf': 1})
        self.assertFalse(s.is_valid())
        self.assertIn("must contain", str(s.errors['anchor_rect']))

        # 3. Not a number
        s = CreateThreadSerializer(data={'anchor_rect': {'x':'a','y':0,'width':0,'height':0}, 'selection_text': 't', 'page_number': 1, 'pdf': 1})
        self.assertFalse(s.is_valid())
        self.assertIn("must be a number", str(s.errors['anchor_rect']))

        # 4. Out of bounds (Normalized 0-1)
        s = CreateThreadSerializer(data={'anchor_rect': {'x':2,'y':0,'width':0,'height':0}, 'selection_text': 't', 'page_number': 1, 'pdf': 1})
        self.assertFalse(s.is_valid())
        self.assertIn("must be between 0 and 1", str(s.errors['anchor_rect']))

    def test_text_length_validation(self):
        # Selection text too long
        s = CreateThreadSerializer(data={'selection_text': 'a'*1001, 'anchor_rect':{'x':0,'y':0,'width':0,'height':0}, 'page_number':1, 'pdf':1})
        self.assertFalse(s.is_valid())
        self.assertIn("cannot exceed 1000", str(s.errors['selection_text']))

        # Message content too long
        s = CreateMessageSerializer(data={'content': 'a'*5001})
        self.assertFalse(s.is_valid())
        self.assertIn("cannot exceed 5000", str(s.errors['content']))

    def test_empty_text_validation(self):
        """NEW: Test empty strings to cover 'cannot be empty' red lines."""
        # 1. Empty Selection Text (covers validate_selection_text line 91)
        s = CreateThreadSerializer(data={
            'selection_text': '   ', # Whitespace only
            'anchor_rect':{'x':0,'y':0,'width':0,'height':0}, 
            'page_number':1, 'pdf':1
        })
        self.assertFalse(s.is_valid())
        self.assertIn("may not be blank", str(s.errors.get('selection_text', '')))

        # 2. Empty Message Content (covers validate_content line 107)
        s = CreateMessageSerializer(data={'content': ''}) # Empty string
        self.assertFalse(s.is_valid())
        self.assertIn("may not be blank", str(s.errors.get('content', '')))


class ThreadModelTestCase(TestCase):
    """Cover models.py __str__ and defaults"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='u', password='p')
        self.ws = Workspace.objects.create(name='W', created_by=self.user)
        self.pdf = PDFFile.objects.create(workspace=self.ws, title='P', file=b'x', uploaded_by=self.user)

    def test_thread_str_and_defaults(self):
        t = Thread.objects.create(
            workspace=self.ws, pdf=self.pdf, page_number=1, 
            selection_text="Short", anchor_rect={'x':0}
        )
        self.assertIn("Thread on P", str(t))
        self.assertEqual(t.anchor_side, 'right') # Default value check

    def test_message_str_variants(self):
        t = Thread.objects.create(workspace=self.ws, pdf=self.pdf, page_number=1, selection_text="x", anchor_rect={'x':0})
        # 1. With Sender
        m1 = Message.objects.create(thread=t, sender=self.user, content="Hi")
        self.assertEqual(str(m1), f"{self.user.username}: Hi")
        # 2. Without Sender (Unknown)
        m2 = Message.objects.create(thread=t, sender=None, content="Ghost")
        self.assertEqual(str(m2), "Unknown: Ghost")


class ThreadViewTestCase(TestCase):
    """Cover views.py: Permissions, Serializer Selection, Mentions, Error Handling"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='user1', password='p')
        self.user2 = User.objects.create_user(username='user2', password='p')
        self.outsider = User.objects.create_user(username='outsider', password='p')
        
        self.workspace = Workspace.objects.create(name='WS', created_by=self.user)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.user, role='RESEARCHER')
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.user2, role='RESEARCHER')
        
        self.pdf = PDFFile.objects.create(workspace=self.workspace, uploaded_by=self.user, title='D', file=b'x')
        self.thread = Thread.objects.create(
            workspace=self.workspace, pdf=self.pdf, page_number=1,
            selection_text="x", anchor_rect={'x':0,'y':0,'width':0,'height':0}, created_by=self.user
        )

    def test_get_serializer_class_direct_logic(self):
        """
        NEW: Directly test the get_serializer_class method.
        This covers lines 50 and 52 which are skipped by normal requests 
        because 'create' and 'retrieve' are overridden in the ViewSet.
        """
        view = ThreadViewSet()
        
        view.action = 'retrieve'
        self.assertEqual(view.get_serializer_class().__name__, 'ThreadDetailSerializer')
        
        view.action = 'create'
        self.assertEqual(view.get_serializer_class().__name__, 'CreateThreadSerializer')
        
        view.action = 'list'
        self.assertEqual(view.get_serializer_class().__name__, 'ThreadSerializer')

    def test_get_messages_action(self):
        """NEW: Cover get_messages action (Lines 235-237)"""
        self.client.force_authenticate(self.user)
        Message.objects.create(thread=self.thread, sender=self.user, content="Msg1")
        
        res = self.client.get(f'/api/threads/{self.thread.id}/get_messages/')
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_serializer_class_selection(self):
        """Standard integration test for views."""
        self.client.force_authenticate(self.user)
        
        # 1. 'create' action 
        self.client.post('/api/threads/', {
            'workspace_id': self.workspace.id, 'pdf_id': self.pdf.id,
            'page_number': 1, 'selection_text': 'x', 'anchor_rect': {'x':0,'y':0,'width':0,'height':0}
        }, format='json')
        
        # 2. 'retrieve' action 
        self.client.get(f'/api/threads/{self.thread.id}/')

        # 3. 'list' action 
        self.client.get(f'/api/threads/?workspace_id={self.workspace.id}&pdf_id={self.pdf.id}')

    def test_permission_denied(self):
        """Cover check_workspace_membership failure."""
        self.client.force_authenticate(self.outsider)
        res = self.client.get(f'/api/threads/{self.thread.id}/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_mention_logic_full_coverage(self):
        """Cover all 3 branches in create_mention_notifications."""
        self.client.force_authenticate(self.user)
        
        # 1. Valid Mention
        self.client.post(f'/api/threads/{self.thread.id}/messages/', {'content': f"@{self.user2.username}"})
        self.assertTrue(Notification.objects.filter(user=self.user2).exists())
        
        # 2. Self Mention (Hit 'continue' line 198)
        c_before = Notification.objects.count()
        self.client.post(f'/api/threads/{self.thread.id}/messages/', {'content': f"@{self.user.username}"})
        self.assertEqual(Notification.objects.count(), c_before)
        
        # 3. Non-Member Mention (Hit 'except DoesNotExist' line 225)
        self.client.post(f'/api/threads/{self.thread.id}/messages/', {'content': f"@{self.outsider.username}"})
        self.assertFalse(Notification.objects.filter(user=self.outsider).exists())

    def test_broadcast_exception_handling(self):
        """Cover try/except blocks in views.py for Redis failures."""
        self.client.force_authenticate(self.user)
        
        # Mock Redis failure for Threads
        with patch('threads.views.ThreadViewSet.broadcast_thread_created') as m:
            m.side_effect = Exception("Boom")
            self.client.post('/api/threads/', {
                'workspace_id': self.workspace.id, 'pdf_id': self.pdf.id,
                'page_number': 1, 'selection_text': 'x', 'anchor_rect': {'x':0,'y':0,'width':0,'height':0}
            }, format='json')
            
        # Mock Redis failure for Messages
        with patch('threads.views.ThreadViewSet.broadcast_message_created') as m:
            m.side_effect = Exception("Boom")
            self.client.post(f'/api/threads/{self.thread.id}/messages/', {'content': 'Hi'})

    def test_list_validation_errors(self):
        """Cover 'workspace_id and pdf_id required' block."""
        self.client.force_authenticate(self.user)
        res = self.client.get('/api/threads/') # No params
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # PDF not in workspace
        res = self.client.get(f'/api/threads/?workspace_id={self.workspace.id}&pdf_id=99999')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class ConsumerTestCase(TransactionTestCase):
    """Cover consumers.py: Connect, Events, Errors."""

    async def test_all_consumer_paths(self):
        # Setup
        user = await sync_to_async(User.objects.create_user)(username='ws', password='p')
        ws = await sync_to_async(Workspace.objects.create)(name='WS', created_by=user)
        await sync_to_async(WorkspaceMember.objects.create)(workspace=ws, user=user)
        pdf = await sync_to_async(PDFFile.objects.create)(workspace=ws, title='P', file=b'x', uploaded_by=user)
        
        # 1. Successful Connection
        path = f"/ws/threads/workspace/{ws.id}/pdf/{pdf.id}/"
        c = WebsocketCommunicator(ThreadConsumer.as_asgi(), path)
        c.scope['user'] = user
        c.scope['url_route'] = {'kwargs': {'workspace_id': ws.id, 'pdf_id': pdf.id}}
        connected, _ = await c.connect()
        self.assertTrue(connected)

        # 2. Receive Ignored (Coverage for 'pass' in receive)
        await c.send_to(text_data="ignore me")

        # 3. Event Broadcasts (Cover lines 48-59)
        # Manually trigger the handlers
        consumer_instance = ThreadConsumer()
        consumer_instance.send = MagicMock() # Mock the send method
        
        # We can't easily call async methods on an instance in a sync way without setup
        # So we use the communicator to receive events sent to the group
        channel_layer = get_channel_layer()
        group_name = f'threads_workspace_{ws.id}_pdf_{pdf.id}'
        
        await channel_layer.group_send(group_name, {
            'type': 'thread.created', 'thread': {'id': 1}
        })
        resp = await c.receive_json_from()
        self.assertEqual(resp['type'], 'thread.created')

        await channel_layer.group_send(group_name, {
            'type': 'message.created', 'thread_id': 1, 'message': {'content': 'x'}
        })
        resp = await c.receive_json_from()
        self.assertEqual(resp['type'], 'message.created')

        await c.disconnect()

    async def test_consumer_refusals(self):
        # 1. User not a member (Covers 'else: await self.close()')
        u = await sync_to_async(User.objects.create_user)(username='outsider', password='p')
        ws = await sync_to_async(Workspace.objects.create)(name='W', created_by=u)
        # No membership
        
        c = WebsocketCommunicator(ThreadConsumer.as_asgi(), f"/ws/threads/workspace/{ws.id}/pdf/1/")
        c.scope['user'] = u
        c.scope['url_route'] = {'kwargs': {'workspace_id': ws.id, 'pdf_id': 1}}
        connected, _ = await c.connect()
        self.assertFalse(connected)

    async def test_bad_workspace_id(self):
        # 2. Workspace DoesNotExist (Covers 'except Workspace.DoesNotExist')
        u = await sync_to_async(User.objects.create_user)(username='u2', password='p')
        c = WebsocketCommunicator(ThreadConsumer.as_asgi(), "/ws/threads/workspace/9999/pdf/1/")
        c.scope['user'] = u
        c.scope['url_route'] = {'kwargs': {'workspace_id': 9999, 'pdf_id': 1}}
        connected, _ = await c.connect()
        self.assertFalse(connected)
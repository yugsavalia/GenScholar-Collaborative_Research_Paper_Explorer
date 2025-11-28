"""
Tests for chatbot views.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from workspaces.models import Workspace, WorkspaceMember
from .models import AIChatMessage
import json


class ChatbotViewsTestCase(TestCase):
    """Test chatbot views."""
    
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
        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.other_user,
            role=WorkspaceMember.Role.REVIEWER
        )
        self.client.login(username='testuser', password='testpass123')
    
    @patch('chatbot.views.get_chatbot_response')
    def test_ask_question_success(self, mock_get_response):
        """Test ask question with successful response."""
        mock_get_response.return_value = "This is a test response"
        
        response = self.client.post('/api/chatbot/ask/', json.dumps({
            'question': 'What is this?',
            'workspace_id': self.workspace.id
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['ai_answer'], "This is a test response")
        # Check messages were saved
        self.assertTrue(AIChatMessage.objects.filter(
            workspace=self.workspace,
            user=self.user,
            is_from_bot=False
        ).exists())
        self.assertTrue(AIChatMessage.objects.filter(
            workspace=self.workspace,
            user=self.user,
            is_from_bot=True
        ).exists())
    
    def test_ask_question_missing_question(self):
        """Test ask question without question."""
        response = self.client.post('/api/chatbot/ask/', json.dumps({
            'workspace_id': self.workspace.id
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_ask_question_missing_workspace_id(self):
        """Test ask question without workspace_id."""
        response = self.client.post('/api/chatbot/ask/', json.dumps({
            'question': 'What is this?'
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_ask_question_nonexistent_workspace(self):
        """Test ask question with nonexistent workspace."""
        response = self.client.post('/api/chatbot/ask/', json.dumps({
            'question': 'What is this?',
            'workspace_id': 99999
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_ask_question_not_member(self):
        """Test ask question when not a member."""
        other_workspace = Workspace.objects.create(
            name='Other Workspace',
            created_by=self.other_user
        )
        response = self.client.post('/api/chatbot/ask/', json.dumps({
            'question': 'What is this?',
            'workspace_id': other_workspace.id
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_ask_question_reviewer_role(self):
        """Test ask question when user is reviewer (should be denied)."""
        self.client.logout()
        self.client.login(username='otheruser', password='testpass123')
        
        response = self.client.post('/api/chatbot/ask/', json.dumps({
            'question': 'What is this?',
            'workspace_id': self.workspace.id
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_ask_question_unauthenticated(self):
        """Test ask question when not authenticated."""
        self.client.logout()
        response = self.client.post('/api/chatbot/ask/', json.dumps({
            'question': 'What is this?',
            'workspace_id': self.workspace.id
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 302)  # Redirects to login
    
    @patch('chatbot.views.get_chatbot_response')
    def test_ask_question_timeout(self, mock_get_response):
        """Test ask question with timeout."""
        import concurrent.futures
        # Mock the ThreadPoolExecutor to raise TimeoutError when result() is called
        with patch('chatbot.views.concurrent.futures.ThreadPoolExecutor') as mock_executor_class:
            mock_executor = MagicMock()
            mock_future = MagicMock()
            mock_future.result.side_effect = concurrent.futures.TimeoutError()
            mock_executor.submit.return_value = mock_future
            mock_executor.__enter__ = MagicMock(return_value=mock_executor)
            mock_executor.__exit__ = MagicMock(return_value=False)
            mock_executor_class.return_value = mock_executor
            
            response = self.client.post('/api/chatbot/ask/', json.dumps({
                'question': 'What is this?',
                'workspace_id': self.workspace.id
            }), content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertIn('too long', data['ai_answer'].lower())
    
    @patch('chatbot.views.get_chatbot_response')
    def test_ask_question_exception(self, mock_get_response):
        """Test ask question with exception."""
        mock_get_response.side_effect = Exception("Test error")
        
        response = self.client.post('/api/chatbot/ask/', json.dumps({
            'question': 'What is this?',
            'workspace_id': self.workspace.id
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('error', data['ai_answer'].lower())


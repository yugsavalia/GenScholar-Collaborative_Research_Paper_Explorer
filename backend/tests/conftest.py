"""
Pytest configuration and shared fixtures.
"""
import pytest
from django.contrib.auth.models import User
from workspaces.models import Workspace, WorkspaceMember
from pdfs.models import PDFFile


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def user2(db):
    """Create a second test user."""
    return User.objects.create_user(
        username='testuser2',
        email='test2@example.com',
        password='testpass123'
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def workspace(db, user):
    """Create a test workspace."""
    return Workspace.objects.create(
        name='Test Workspace',
        created_by=user
    )


@pytest.fixture
def workspace_member(db, workspace, user):
    """Create a workspace member."""
    return WorkspaceMember.objects.create(
        workspace=workspace,
        user=user,
        role=WorkspaceMember.Role.RESEARCHER
    )


@pytest.fixture
def pdf_file(db, workspace, user):
    """Create a test PDF file."""
    return PDFFile.objects.create(
        workspace=workspace,
        uploaded_by=user,
        title='Test PDF',
        file=b'%PDF-1.4 fake pdf content'
    )


@pytest.fixture
def authenticated_client(db, client, user):
    """Create an authenticated test client."""
    client.force_login(user)
    return client


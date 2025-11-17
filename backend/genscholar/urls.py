"""
URL configuration for genscholar project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from accounts import views as accounts_views
from api import views as api_views
from chatbot import views as chatbot_views
from workspaces import views as workspace_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # API routes for frontend integration
    path('api/auth/csrf/', accounts_views.api_csrf_view, name='api_csrf'),
    path('api/auth/login/', accounts_views.api_login_view, name='api_login'),
    path('api/auth/signup/', accounts_views.api_signup_view, name='api_signup'),
    path('api/auth/logout/', accounts_views.api_logout_view, name='api_logout'),
    path('api/auth/user/', accounts_views.api_get_user_view, name='api_get_user'),
    path('api/workspaces/', workspace_views.api_workspaces_view, name='api_workspaces'),
    # Workspace member management API endpoints
    path('api/workspaces/<int:workspace_id>/members/', api_views.api_workspace_members_view, name='api_workspace_members'),
    path('api/workspaces/<int:workspace_id>/invite/', api_views.api_workspace_invite_view, name='api_workspace_invite'),
    path('api/workspaces/<int:workspace_id>/members/<int:member_id>/', api_views.api_workspace_member_role_view, name='api_workspace_member_role'),
    # Invitation and notification API endpoints
    path('api/invitations/', api_views.api_invitations_view, name='api_invitations'),
    path('api/invitations/<int:invitation_id>/accept/', api_views.api_accept_invitation_view, name='api_accept_invitation'),
    path('api/invitations/<int:invitation_id>/decline/', api_views.api_decline_invitation_view, name='api_decline_invitation'),
    path('api/notifications/', api_views.api_notifications_view, name='api_notifications'),
    path('api/notifications/<int:notification_id>/', api_views.api_mark_notification_read_view, name='api_mark_notification_read'),
    # Existing routes
    path('accounts/', include('accounts.urls')),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', include('workspaces.urls')),
    path('pdfs/', include('pdfs.urls')),
    path('workspace/<int:workspace_id>/delete/', workspace_views.delete_workspace_view, name='delete_workspace'),
    path('api/chatbot/ask/', chatbot_views.ask_question, name='chatbot_ask'),
    # DRF API router (includes /api/users/, /api/workspaces/, /api/pdfs/, etc.)
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

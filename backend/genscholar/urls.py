"""
URL configuration for genscholar project.

The `urlpatterns` list routes URLs to views.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from accounts import views as accounts_views
from api import views as api_views
from api.auth_password_views import request_password_reset, confirm_password_reset
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
    path('api/auth/request-email-verification/', accounts_views.api_request_email_verification_view, name='api_request_email_verification'),
    path('api/auth/verify-email/', accounts_views.api_verify_email_token_view, name='api_verify_email_token'),
    path('api/auth/verify-otp/', accounts_views.api_verify_otp_view, name='api_verify_otp'),

    # Password reset endpoints
    path('api/auth/password-reset/', request_password_reset, name='api_password_reset'),
    path('api/auth/password-reset/confirm/', confirm_password_reset, name='api_password_reset_confirm'),

    path('api/profile/me/', accounts_views.api_profile_view, name='api_profile'),

    # Workspace management
    path('api/workspaces/', workspace_views.api_workspaces_view, name='api_workspaces'),
    path('api/workspaces/<int:workspace_id>/', workspace_views.api_delete_workspace_view, name='api_delete_workspace'),

    # Workspace member API
    path('api/workspaces/<int:workspace_id>/members/', api_views.api_workspace_members_view, name='api_workspace_members'),
    path('api/workspaces/<int:workspace_id>/mentionable-users/', api_views.api_workspace_mentionable_users_view, name='api_workspace_mentionable_users'),
    path('api/workspaces/<int:workspace_id>/pinned-note/', api_views.api_workspace_pinned_note_view, name='api_workspace_pinned_note'),
    path('api/workspaces/<int:workspace_id>/invite/', api_views.api_workspace_invite_view, name='api_workspace_invite'),
    path('api/workspaces/<int:workspace_id>/members/<int:member_id>/', api_views.api_workspace_member_role_view, name='api_workspace_member_role'),

    # Invitations & notifications
    path('api/invitations/', api_views.api_invitations_view, name='api_invitations'),
    path('api/invitations/<int:invitation_id>/accept/', api_views.api_accept_invitation_view, name='api_accept_invitation'),
    path('api/invitations/<int:invitation_id>/decline/', api_views.api_decline_invitation_view, name='api_decline_invitation'),
    path('api/notifications/', api_views.api_notifications_view, name='api_notifications'),
    path('api/notifications/<int:notification_id>/', api_views.api_mark_notification_read_view, name='api_mark_notification_read'),

    # ============================
    #   IMPORTANT: FIXED ROUTE
    # ============================
    # This MUST appear BEFORE the catch-all "api/" includes.
    path("api/update-credentials", accounts_views.api_update_credentials_view, name="api_update_credentials"),

    # Existing routes
    path('accounts/', include('accounts.urls')),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # django-allauth URLs
    path('accounts/', include('allauth.urls')),

    # Workspace URLs
    path('', include('workspaces.urls')),

    # PDFs & chatbot
    path('pdfs/', include('pdfs.urls')),
    path('workspace/<int:workspace_id>/delete/', workspace_views.delete_workspace_view, name='delete_workspace'),
    path('api/chatbot/ask/', chatbot_views.ask_question, name='chatbot_ask'),

    # ================
    #   DRF Routers
    # ================
    path('api/', include('api.urls')),        # MUST come after update-credentials
    path('api/', include('threads.urls')),    # MUST come after update-credentials
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

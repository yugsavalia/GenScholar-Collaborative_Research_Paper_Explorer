from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('request-email-verification/', views.request_email_verification, name='request_email_verification'),
    path('verify-email/', views.verify_email_token, name='verify_email_token'),
    path('login/', views.login_view, name='login'),
    path('resend-verification/', views.resend_verification_email_view, name='resend_verification'),
]




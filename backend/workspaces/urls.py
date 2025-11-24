from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('create/', views.create_workspace_view, name='create_workspace'),
    path('<int:workspace_id>/', views.workspace_detail_view, name='workspace_detail'),
    path('<int:workspace_id>/invite/', views.invite_to_workspace_view, name='invite_to_workspace'),
    path('<int:workspace_id>/change-role/', views.change_member_role_view, name='change_member_role'),
]




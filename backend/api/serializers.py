from django.contrib.auth.models import User
from rest_framework import serializers

from workspaces.models import Workspace, WorkspaceMember
from pdfs.models import PDFFile, Annotation
from chat.models import ChatMessage


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class WorkspaceMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = WorkspaceMember
        fields = ['id', 'workspace', 'user', 'role', 'joined_at']


class WorkspaceSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    members = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = ['id', 'name', 'created_by', 'created_at', 'members']

    def get_members(self, obj):
        # Return full member information including roles
        memberships = WorkspaceMember.objects.filter(workspace=obj).select_related('user')
        return WorkspaceMemberSerializer(memberships, many=True).data


class PDFSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = PDFFile
        fields = ['id', 'title', 'file', 'uploaded_by', 'workspace', 'uploaded_at']


class AnnotationSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Annotation
        fields = ['id', 'pdf', 'page_number', 'coordinates', 'comment', 'created_by', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'workspace', 'user', 'message', 'timestamp']


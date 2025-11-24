import re
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from rest_framework import serializers

from workspaces.models import Workspace, WorkspaceMember, validate_workspace_name
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
        extra_kwargs = {
            'name': {'validators': [validate_workspace_name]}
        }

    def validate_name(self, value):
        """Validate workspace name according to strict rules."""
        if value:
            try:
                validate_workspace_name(value)
            except ValidationError as e:
                error_message = e.messages[0] if hasattr(e, 'messages') and e.messages else str(e)
                raise serializers.ValidationError(error_message)
        return value

    def get_members(self, obj):
        # Return full member information including roles
        memberships = WorkspaceMember.objects.filter(workspace=obj).select_related('user')
        return WorkspaceMemberSerializer(memberships, many=True).data


class PDFSerializer(serializers.ModelSerializer):
    """Serializer for PDF metadata only - excludes binary file data."""
    uploaded_by = UserSerializer(read_only=True)
    name = serializers.CharField(source='title', read_only=True)

    class Meta:
        model = PDFFile
        fields = ['id', 'name', 'title', 'uploaded_by', 'workspace', 'uploaded_at', 'is_indexed']
        read_only_fields = ['id', 'uploaded_at', 'is_indexed']
        # Explicitly exclude 'file' field (BinaryField) - must use /api/pdfs/<id>/download/ endpoint
        extra_kwargs = {
            'file': {'write_only': True}  # Only for creation, never in response
        }
    
    def to_representation(self, instance):
        """Ensure file field is never included in serialized output."""
        data = super().to_representation(instance)
        # Double-check: remove 'file' if it somehow got included
        data.pop('file', None)
        return data


class AnnotationSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    # Accept frontend field names and convert them
    quads = serializers.JSONField(write_only=True, required=False)
    selected_text = serializers.CharField(write_only=True, required=False, allow_blank=True)
    type = serializers.CharField(write_only=True, required=False)
    color = serializers.CharField(write_only=True, required=False)
    # Make coordinates optional when quads is provided
    coordinates = serializers.JSONField(required=False)

    class Meta:
        model = Annotation
        fields = ['id', 'pdf', 'page_number', 'coordinates', 'comment', 'created_by', 'created_at', 'quads', 'selected_text', 'type', 'color']
        read_only_fields = ['id', 'created_by', 'created_at']

    def validate(self, data):
        # Ensure either coordinates or quads is provided
        if 'coordinates' not in data and 'quads' not in data:
            raise serializers.ValidationError("Either 'coordinates' or 'quads' must be provided.")
        return data

    def create(self, validated_data):
        # Extract frontend-specific fields
        quads = validated_data.pop('quads', None)
        selected_text = validated_data.pop('selected_text', None)
        annotation_type = validated_data.pop('type', None)
        color = validated_data.pop('color', None)
        
        # Convert quads to coordinates format expected by backend
        if quads is not None:
            # Store quads as coordinates (quads is already a JSON structure)
            # Also include metadata in coordinates
            coords = {
                'quads': quads,
            }
            if annotation_type:
                coords['type'] = annotation_type
            if color:
                coords['color'] = color
            validated_data['coordinates'] = coords
        elif 'coordinates' not in validated_data:
            # If no coordinates provided, use empty dict
            validated_data['coordinates'] = {}
        
        # Convert selected_text to comment
        if selected_text is not None:
            validated_data['comment'] = selected_text
        elif 'comment' not in validated_data:
            validated_data['comment'] = ''
        
        return super().create(validated_data)


class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'workspace', 'user', 'message', 'timestamp']


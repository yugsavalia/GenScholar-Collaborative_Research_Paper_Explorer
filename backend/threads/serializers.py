from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Thread, Message


class UserSerializer(serializers.ModelSerializer):
    """Simple user serializer for thread/message authors."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for thread messages."""
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'thread', 'sender', 'content', 'created_at', 'edited_at']
        read_only_fields = ['id', 'created_at', 'edited_at']


class ThreadSerializer(serializers.ModelSerializer):
    """Serializer for threads."""
    created_by = UserSerializer(read_only=True)
    pdf_title = serializers.CharField(source='pdf.title', read_only=True)
    message_count = serializers.SerializerMethodField()
    last_message_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = Thread
        fields = [
            'id', 'workspace', 'pdf', 'pdf_title', 'page_number',
            'selection_text', 'anchor_rect', 'anchor_side',
            'created_by', 'created_at', 'last_activity_at',
            'message_count', 'last_message_preview'
        ]
        read_only_fields = ['id', 'created_at', 'last_activity_at']
    
    def get_message_count(self, obj):
        """Get the number of messages in this thread."""
        return obj.messages.count()
    
    def get_last_message_preview(self, obj):
        """Get a preview of the last message."""
        last_message = obj.messages.last()
        if last_message:
            return {
                'content': last_message.content[:100],
                'sender': last_message.sender.username if last_message.sender else None,
                'created_at': last_message.created_at.isoformat()
            }
        return None


class ThreadDetailSerializer(ThreadSerializer):
    """Detailed thread serializer with all messages."""
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta(ThreadSerializer.Meta):
        fields = ThreadSerializer.Meta.fields + ['messages']


class CreateThreadSerializer(serializers.ModelSerializer):
    """Serializer for creating a new thread."""
    class Meta:
        model = Thread
        fields = ['pdf', 'page_number', 'selection_text', 'anchor_rect', 'anchor_side']
    
    def validate_anchor_rect(self, value):
        """Validate anchor_rect structure."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("anchor_rect must be a JSON object")
        
        required_keys = ['x', 'y', 'width', 'height']
        for key in required_keys:
            if key not in value:
                raise serializers.ValidationError(f"anchor_rect must contain '{key}'")
            if not isinstance(value[key], (int, float)):
                raise serializers.ValidationError(f"anchor_rect.{key} must be a number")
            # Validate normalized coordinates (0-1)
            if key in ['x', 'y', 'width', 'height']:
                if value[key] < 0 or value[key] > 1:
                    raise serializers.ValidationError(f"anchor_rect.{key} must be between 0 and 1 (normalized)")
        
        return value
    
    def validate_selection_text(self, value):
        """Sanitize and validate selection text."""
        if not value or not value.strip():
            raise serializers.ValidationError("selection_text cannot be empty")
        # Limit length to prevent abuse
        if len(value) > 1000:
            raise serializers.ValidationError("selection_text cannot exceed 1000 characters")
        return value.strip()


class CreateMessageSerializer(serializers.ModelSerializer):
    """Serializer for creating a new message."""
    class Meta:
        model = Message
        fields = ['content']
    
    def validate_content(self, value):
        """Validate message content."""
        if not value or not value.strip():
            raise serializers.ValidationError("Message content cannot be empty")
        # Limit length to prevent abuse
        if len(value) > 5000:
            raise serializers.ValidationError("Message content cannot exceed 5000 characters")
        return value.strip()


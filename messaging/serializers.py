from rest_framework import serializers
from .models import Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id','sender', 'recipient', 'content', 'timestamp', 'is_read', 'is_system_message']
        extra_kwargs = {
            'sender': {'required': False, 'allow_null': True},
        }

    def validate(self, data):
        # If it's not a system message, ensure a sender is provided
        if not data.get('is_system_message') and not data.get('sender'):
            raise serializers.ValidationError("Sender is required for non-system messages.")
        return data

from rest_framework import serializers
from .models import SynthesiaVideo


class SynthesiaVideoSerializer(serializers.ModelSerializer):
    # Map camelCase field names from frontend to snake_case in Django model
    aspectRatio = serializers.CharField(source='aspect_ratio')
    scriptText = serializers.CharField(source='script_text')
    avatarSettings = serializers.JSONField(source='avatar_settings')
    backgroundSettings = serializers.JSONField(source='background_settings')
    secure_download_url = serializers.SerializerMethodField()
    secure_thumbnail_image = serializers.SerializerMethodField()
    secure_thumbnail_gif = serializers.SerializerMethodField()

    class Meta:
        model = SynthesiaVideo
        fields = [
            'id', 'synthesia_id', 'title', 'description', 'visibility', 'aspectRatio', 'test',
            'download_url', 'scheduled_time', 'scriptText', 'avatar', 'avatarSettings',
            'background', 'backgroundSettings', 'whatsapp_number', 'status', 'created_at', 
            'secure_download_url', 'secure_thumbnail_image', 'secure_thumbnail_gif'
        ]
        read_only_fields = [
            'id', 'status', 'created_at',
            'secure_download_url',
            'secure_thumbnail_image',
            'secure_thumbnail_gif'
        ]

    def validate(self, data):
        # Ensure avatar_settings has correct structure if provided
        if 'avatar_settings' not in data or not data['avatar_settings']:
            data['avatar_settings'] = {
                "horizontalAlign": "center",
                "scale": 1,
                "style": "rectangular",
                "seamless": False
            }

        # Ensure background_settings has correct structure if provided
        if 'background_settings' not in data or not data['background_settings']:
            data['background_settings'] = {
                "videoSettings": {
                    "shortBackgroundContentMatchMode": "freeze",
                    "longBackgroundContentMatchMode": "trim"
                }
            }

        return data

    def to_internal_value(self, data):
        # Handle the nested 'input' field from the frontend
        if 'input' in data and isinstance(data['input'], list) and len(data['input']) > 0:
            input_data = data['input'][0]
            # Map input fields to top-level fields
            data['scriptText'] = input_data.get('scriptText')
            data['avatar'] = input_data.get('avatar')
            data['avatarSettings'] = input_data.get('avatarSettings')
            data['background'] = input_data.get('background')
            data['backgroundSettings'] = input_data.get('backgroundSettings')
            # Remove the input field as we've extracted what we need
            del data['input']

        return super().to_internal_value(data)

    def get_secure_download_url(self, obj):
        return obj.get_secure_download_url()

    def get_secure_thumbnail_image(self, obj):
        return obj.get_secure_thumbnail_image()

    def get_secure_thumbnail_gif(self, obj):
        return obj.get_secure_thumbnail_gif()


class SynthesiaVideoStatusSerializer(serializers.ModelSerializer):
    secure_download_url = serializers.SerializerMethodField()
    secure_thumbnail_image = serializers.SerializerMethodField()
    secure_thumbnail_gif = serializers.SerializerMethodField()

    class Meta:
        model = SynthesiaVideo
        fields = [
            'id', 'status', 'secure_download_url',
            'secure_thumbnail_image', 'secure_thumbnail_gif',
            'duration', 'error_message', 'is_ready_for_whatsapp',
            'scheduled_time', 'whatsapp_sent_at'
        ]

    def get_secure_download_url(self, obj):
        return obj.get_secure_download_url()

    def get_secure_thumbnail_image(self, obj):
        return obj.get_secure_thumbnail_image()

    def get_secure_thumbnail_gif(self, obj):
        return obj.get_secure_thumbnail_gif()

from django.db import models
from datahub.models import Contact  # Assuming Contact is in datahub app
from datetime import datetime as dt


class Campaign(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    # Enum for different communication types
    COMMUNICATION_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
    ]
    communication_type = models.CharField(
        max_length=50, choices=COMMUNICATION_TYPES
    )
    scheduled_date = models.DateTimeField(
        null=True, blank=True, help_text="Date to automatically start the campaign.")
    is_manual_start = models.BooleanField(
        default=False, help_text="Indicates if the campaign should be started manually.")
    started_at = models.DateTimeField(
        null=True, blank=True, help_text="Timestamp of when the campaign was started.")

    def __str__(self):
        return self.name


class CampaignMessage(models.Model):
    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="messages")
    subject = models.CharField(
        max_length=255, blank=True, null=True)  # For emails
    template = models.TextField()  # Template content with placeholders
    # For multimedia (video/image) links
    media_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message for {self.campaign.name}"


class CampaignContact(models.Model):
    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="campaign_contacts")
    contact = models.ForeignKey(
        Contact, on_delete=models.CASCADE, related_name="campaigns")
    # Status of message delivery
    status = models.CharField(max_length=50, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.contact} in {self.campaign.name}"


class WaapiInstance(models.Model):
    # The UserProfile associated with this instance
    user_profile = models.OneToOneField(
        'users.UserProfile',  # Fully qualify the reference with the app name
        on_delete=models.CASCADE,
        related_name='waapi_instance'
    )
    instance_id = models.CharField(max_length=100, unique=True)
    # Status e.g., 'qr', 'ready', 'disconnected'
    status = models.CharField(max_length=20, default='qr')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Waapi Instance for {self.user_profile.user.username} - Status: {self.status}"


class SynthesiaVideo(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),  # Before sending to Synthesia
        ('in_progress', 'In Progress'),  # Synthesia status
        ('complete', 'Complete'),  # Synthesia status
        ('sent', 'Sent'),  # Sent via WhatsApp
        ('scheduled', 'scheduled'),  # Scheduled to be Sent via WhatsApp during business hours
        ('failed', 'Failed'),  # Any error occurred
    )

    # Synthesia video details
    synthesia_id = models.CharField(max_length=255, null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    visibility = models.CharField(max_length=20, default='private')
    aspect_ratio = models.CharField(max_length=10, default='16:9')
    test = models.BooleanField(default=False)

    # Script and avatar details (from input array)
    script_text = models.TextField()
    avatar = models.CharField(max_length=255)
    avatar_settings = models.JSONField(default=dict)
    background = models.CharField(max_length=255, default='white_studio')
    background_settings = models.JSONField(default=dict)

    # WhatsApp details
    whatsapp_number = models.CharField(max_length=20)

    # Status and tracking fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    synthesia_created_at = models.BigIntegerField(null=True, blank=True)
    synthesia_last_updated_at = models.BigIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')

    # Response data
    download_url = models.URLField(null=True, blank=True)
    duration = models.CharField(max_length=20, null=True, blank=True)
    thumbnail_image = models.URLField(null=True, blank=True)
    thumbnail_gif = models.URLField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)

    # Added for frontend notification
    scheduled_time = models.DateTimeField(null=True, blank=True)
    is_ready_for_whatsapp = models.BooleanField(
        default=False, help_text="Flag indicating video is ready to send via WhatsApp")
    whatsapp_sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.status}"

    def get_synthesia_payload(self):
        """
        Generate the payload for Synthesia API
        """
        return {
            "test": self.test,
            "title": self.title,
            "description": self.description,
            "visibility": self.visibility,
            "aspectRatio": self.aspect_ratio,
            "input": [
                {
                    "scriptText": self.script_text,
                    "avatar": self.avatar,
                    "avatarSettings": self.avatar_settings,
                    "background": self.background,
                    "backgroundSettings": self.background_settings
                }
            ]
        }

    def update_from_synthesia_response(self, response_data):
        """
        Update model fields from Synthesia API response
        """
        self.synthesia_id = response_data.get('id', self.synthesia_id)
        self.status = response_data.get('status', self.status)

        if response_data.get('createdAt'):
            self.synthesia_created_at = response_data.get('createdAt')

        if response_data.get('lastUpdatedAt'):
            self.synthesia_last_updated_at = response_data.get('lastUpdatedAt')

        if response_data.get('download'):
            self.download_url = response_data.get('download')

        if response_data.get('duration'):
            self.duration = response_data.get('duration')

        if response_data.get('thumbnail'):
            thumbnail = response_data.get('thumbnail', {})
            if thumbnail.get('image'):
                self.thumbnail_image = thumbnail.get('image')
            if thumbnail.get('gif'):
                self.thumbnail_gif = thumbnail.get('gif')

        # Set is_ready_for_whatsapp when video is complete and has download URL
        if response_data.get('status') == 'complete' and response_data.get('download'):
            self.is_ready_for_whatsapp = True

        self.save()

    def mark_as_sent(self):
        """
        Mark the video as sent via WhatsApp
        """
        self.status = 'sent'
        self.whatsapp_sent_at = dt.now()
        self.save()

    def schedule_video(self, scheduled_time):
        """
        Schedule the video to be sent at a specific time.
        """
        if self.scheduled_time:
            raise ValueError("Video is already scheduled.")
        self.scheduled_time = scheduled_time
        self.status = 'scheduled'
        self.save()


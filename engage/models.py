from django.db import models
from datahub.models import Contact  # Assuming Contact is in datahub app
from users.models import UserProfile


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
    scheduled_date = models.DateTimeField(null=True, blank=True, help_text="Date to automatically start the campaign.")
    is_manual_start = models.BooleanField(default=False, help_text="Indicates if the campaign should be started manually.")
    started_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp of when the campaign was started.")

    def __str__(self):
        return self.name

class CampaignMessage(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="messages")
    subject = models.CharField(max_length=255, blank=True, null=True)  # For emails
    template = models.TextField()  # Template content with placeholders
    media_url = models.URLField(blank=True, null=True)  # For multimedia (video/image) links
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message for {self.campaign.name}"

class CampaignContact(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="campaign_contacts")
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name="campaigns")
    status = models.CharField(max_length=50, default="pending")  # Status of message delivery
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
    status = models.CharField(max_length=20, default='qr')  # Status e.g., 'qr', 'ready', 'disconnected'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Waapi Instance for {self.user_profile.user.username} - Status: {self.status}"

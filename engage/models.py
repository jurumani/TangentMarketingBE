from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import logging
from django.conf import settings
import base64
import hmac
import hashlib
from django.db import models
from datahub.models import Contact  # Assuming Contact is in datahub app
from datetime import datetime as dt
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


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
        # Scheduled to be Sent via WhatsApp during business hours
        ('scheduled', 'scheduled'),
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

    # Add these new fields for encrypted storage
    encrypted_download_url = models.BinaryField(null=True, blank=True)
    encrypted_thumbnail_image = models.BinaryField(null=True, blank=True)
    encrypted_thumbnail_gif = models.BinaryField(null=True, blank=True)

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
            # Encrypt the download URL
            download_url = response_data.get('download')
            self.encrypted_download_url = self._encrypt_url(download_url)
            # Store a non-sensitive version for reference/display
            self.download_url = self._sanitize_url(download_url)

        if response_data.get('duration'):
            self.duration = response_data.get('duration')

        if response_data.get('thumbnail'):
            thumbnail = response_data.get('thumbnail', {})
            if thumbnail.get('image'):
                image_url = thumbnail.get('image')
                self.encrypted_thumbnail_image = self._encrypt_url(image_url)
                self.thumbnail_image = self._sanitize_url(image_url)

            if thumbnail.get('gif'):
                gif_url = thumbnail.get('gif')
                self.encrypted_thumbnail_gif = self._encrypt_url(gif_url)
                self.thumbnail_gif = self._sanitize_url(gif_url)

        # Set is_ready_for_whatsapp when video is complete and has download URL
        if response_data.get('status') == 'complete' and self.encrypted_download_url:
            self.is_ready_for_whatsapp = True

        self.save()

    def _encrypt_url(self, url):
        """
        Encrypt a URL containing sensitive information

        Args:
            url: URL with sensitive information

        Returns:
            Encrypted URL as binary data
        """
        if not url:
            return None

        try:
            # Make sure the key is in the correct format
            key = settings.URL_ENCRYPTION_KEY
            if isinstance(key, str):
                key = key.encode()

            f = Fernet(key)

            # Encrypt the URL
            encrypted_url = f.encrypt(url.encode('utf-8'))
            return encrypted_url
        except Exception as e:
            # Log the error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Encryption error: {e}")

            # Return None or handle the error appropriately
            return None

    def _decrypt_url(self, encrypted_url):
        """
        Decrypt an encrypted URL

        Args:
            encrypted_url: Encrypted URL binary data

        Returns:
            Original URL string
        """
        try:
            # Make sure the key is in the correct format
            key = settings.URL_ENCRYPTION_KEY
            if isinstance(key, str):
                key = key.encode()

            f = Fernet(key)

            # Encrypt the URL
            decrypted_url = f.decrypt(encrypted_url).decode('utf-8')
            return decrypted_url
        except Exception as e:
            # Log the error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Encryption error: {e}")

            # Return None or handle the error appropriately
            return None

    def _sanitize_url(self, url):
        """
        Create a sanitized version of the URL for reference/display

        Args:
            url: Original URL with sensitive information

        Returns:
            URL without sensitive information
        """
        if not url:
            return None

        from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

        # Parse the URL
        parsed_url = urlparse(url)

        # Remove query parameters that might contain credentials
        query_params = parse_qs(parsed_url.query)
        filtered_params = {k: v for k, v in query_params.items()
                           if not k.lower() in ['accesskey', 'secretkey', 'awsaccesskeyid',
                                                'x-amz-security-token', 'sessiontoken']}

        # Reconstruct the URL without sensitive parameters
        sanitized_url = urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            urlencode(filtered_params, doseq=True),
            parsed_url.fragment
        ))

        return sanitized_url

    def _generate_hash(self, url, expiry_time=3600):
        """
        Generate a secure hash for a URL with expiry

        Args:
            url: The URL to hash (string or bytes)
            expiry_time: Time in seconds for URL validity (default 1 hour)

        Returns:
            Tuple of (hash, expiry_timestamp)
        """
        # Get a secret key from settings or define one
        secret_key = getattr(settings, 'URL_HASH_SECRET_KEY',
                             'your-default-secret-key')

        # Generate expiry timestamp
        expires = int(dt.now().timestamp()) + expiry_time

        # Ensure URL is a string
        if isinstance(url, bytes):
            url = url.decode('utf-8')

        # Create the string to hash
        to_hash = f"{url}|{expires}|{self.id}"

        # Generate HMAC hash
        hash_obj = hmac.new(
            secret_key.encode('utf-8'),
            to_hash.encode('utf-8'),
            hashlib.sha256
        )

        # Return the base64 encoded hash and expiry
        hash_value = base64.urlsafe_b64encode(
            hash_obj.digest()).decode('utf-8').rstrip('=')
        return hash_value, expires

    def _add_hash_to_url(self, url, expiry_time=3600):
        """
        Add hash and expiry parameters to URL

        Args:
            url: The original URL (string or bytes)
            expiry_time: Time in seconds for URL validity

        Returns:
            URL with hash and expiry parameters added
        """
        if not url:
            return None

        # Ensure URL is a string
        if isinstance(url, bytes):
            url = url.decode('utf-8')

        hash_value, expires = self._generate_hash(url, expiry_time)

        # Parse the URL
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        # Add our parameters
        query_params['hash'] = [hash_value]
        query_params['expires'] = [str(expires)]
        query_params['video_id'] = [str(self.id)]

        # Reconstruct the URL
        new_query = urlencode(query_params, doseq=True)
        new_url = urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment
        ))

        return new_url

    def get_secure_download_url(self, expiry_time=3600):
        """
        Get download URL with security hash

        Args:
            expiry_time: Time in seconds for URL validity (default 1 hour)

        Returns:
            Secured download URL
        """
        if not self.encrypted_download_url:
            return None

        # Decrypt the original URL
        original_url = self._decrypt_url(self.encrypted_download_url)

        # Add hash for additional security
        return self._add_hash_to_url(original_url, expiry_time)

    def get_secure_thumbnail_image(self, expiry_time=3600):
        """
        Get thumbnail image URL with security hash

        Args:
            expiry_time: Time in seconds for URL validity (default 1 hour)

        Returns:
            Secured thumbnail image URL
        """
        if not self.encrypted_thumbnail_image:
            return None

        original_url = self._decrypt_url(self.encrypted_thumbnail_image)
        return self._add_hash_to_url(original_url, expiry_time)

    def get_secure_thumbnail_gif(self, expiry_time=3600):
        """
        Get thumbnail GIF URL with security hash

        Args:
            expiry_time: Time in seconds for URL validity (default 1 hour)

        Returns:
            Secured thumbnail GIF URL
        """
        if not self.encrypted_thumbnail_gif:
            return None

        original_url = self._decrypt_url(self.encrypted_thumbnail_gif)
        return self._add_hash_to_url(original_url, expiry_time)

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

    @staticmethod
    def verify_url_hash(url, hash_value, expires, video_id):
        """
        Verify if a URL hash is valid

        Args:
            url: The original URL (without hash parameters)
            hash_value: The hash to verify
            expires: Expiry timestamp
            video_id: ID of the video

        Returns:
            Boolean indicating if hash is valid and not expired
        """
        # Check if URL has expired
        current_time = int(dt.now().timestamp())
        if current_time > int(expires):
            return False

        # Get video object
        try:
            SynthesiaVideo.objects.get(id=video_id)
        except SynthesiaVideo.DoesNotExist:
            return False

        # Recreate the hash
        secret_key = getattr(settings, 'URL_HASH_SECRET_KEY',
                             'your-default-secret-key')
        to_hash = f"{url}|{expires}|{video_id}"

        # Generate HMAC hash
        hash_obj = hmac.new(
            secret_key.encode('utf-8'),
            to_hash.encode('utf-8'),
            hashlib.sha256
        )

        # Check if hashes match
        expected_hash = base64.urlsafe_b64encode(
            hash_obj.digest()).decode('utf-8').rstrip('=')
        return hmac.compare_digest(expected_hash, hash_value)

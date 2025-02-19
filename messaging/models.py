from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE, null=True, blank=True)
    recipient = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_system_message = models.BooleanField(default=False)
    message_type = models.CharField(max_length=50, choices=[
        ('informational', 'Informational'),
        ('actionable', 'Actionable'),
    ], default='informational')
    actions = models.JSONField(null=True, blank=True)  # To store actions as JSON (e.g., [{"action": "accept", "label": "Accept"}])

    def __str__(self):
        return f"Message from {self.sender} to {self.recipient} at {self.timestamp}"

    def trigger_action(self, action_type):
        # Logic to trigger action based on action_type.
        # This will be highly customizable.
        pass

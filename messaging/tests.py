from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token  # Token-based authentication
from .models import Message

User = get_user_model()

class MessagingTestCase(APITestCase):

    def setUp(self):
        """
        Set up test data.
        Create a test user, generate a token, and authenticate the client.
        """
        # Create users
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass')

        # Generate token for the user
        self.token = Token.objects.create(user=self.user)

        # Authenticate the client with the token
        self.client = APIClient()  # Create a new APIClient instance
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # Create a sample message with actions
        self.message = Message.objects.create(
            sender=self.user,
            recipient=self.other_user,
            content="This is a test message with actions.",
            is_system_message=False,
            message_type="actionable",
            actions=[{"action": "accept", "label": "Accept"}, {"action": "reject", "label": "Reject"}]
        )

    def test_create_message_with_actions(self):
        """
        Test creating a new message with actions.
        """
        url = '/messaging/messages/'
        data = {
            "recipient": self.other_user.id,
            "content": "This is a new message with actions.",
            "is_system_message": False,
            "message_type": "actionable",
            "actions": [{"action": "accept", "label": "Accept"}, {"action": "reject", "label": "Reject"}]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('actions', response.data)
        self.assertEqual(len(response.data['actions']), 2)

    def test_trigger_message_action(self):
        """
        Test triggering an action from a message.
        """
        url = f'/messaging/messages/{self.message.id}/trigger-action/'
        data = {
            "action": "accept"
        }
        response = self.client.post(url, data, format='json')
        print(response.data)  # Add this to the test_create_message_with_actions method to inspect the error
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], "Action 'accept' performed successfully.")

    def test_invalid_action_trigger(self):
        """
        Test triggering an invalid action from a message.
        """
        url = f'/messaging/messages/{self.message.id}/trigger-action/'
        data = {
            "action": "invalid_action"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Invalid action specified.")

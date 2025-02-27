# tests.py
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from users.models import UserProfile
from engage.models import WaapiInstance
import json
import base64
from engage.views import get_qr_code, check_waapi_status, waapi_webhook, get_instance_id, download_and_convert_to_base64, create_or_get_instance


class EngageViewsTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        # Get or create a UserProfile for the test user
        # This avoids the UNIQUE constraint error
        self.user_profile, created = UserProfile.objects.get_or_create(
            user=self.user)

        # Create a test WaapiInstance
        self.waapi_instance = WaapiInstance.objects.create(
            user_profile=self.user_profile,
            instance_id='test-instance-id',
            status='qr'
        )

        # Set up API client
        self.api_client = APIClient()
        self.api_client.force_authenticate(user=self.user)


class GetQRCodeTestCase(EngageViewsTestCase):
    @patch('engage.views.waapi_request')
    def test_get_qr_code_success(self, mock_waapi_request):
        # Mock the API response for getting a QR code
        mock_waapi_request.return_value = {
            "qrCode": {
                "status": "success",
                "data": {
                    "qr_code": "base64encodedqrcode"
                }
            }
        }

        # Test the API endpoint
        response = self.api_client.get(reverse('get_qr_code'))

        # Check that the response contains the expected data
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['qr_code_url'], "base64encodedqrcode")
        self.assertEqual(response_data['status'], "pending")

        # Verify that waapi_request was called correctly
        mock_waapi_request.assert_called_once_with(
            f"instances/{self.waapi_instance.instance_id}/client/qr")

    @patch('engage.views.waapi_request')
    def test_get_qr_code_create_new_instance(self, mock_waapi_request):
        # Delete any existing instances to test creation flow
        WaapiInstance.objects.filter(user_profile=self.user_profile).delete()

        # Mock the API responses for creating a new instance and getting a QR code
        mock_waapi_request.side_effect = [
            {
                "instance": {
                    "id": "new-instance-id"
                }
            },
            {
                "qrCode": {
                    "status": "success",
                    "data": {
                        "qr_code": "base64encodedqrcode"
                    }
                }
            }
        ]

        # Test the API endpoint
        response = self.api_client.get(reverse('get_qr_code'))

        # Check that the response contains the expected data
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['qr_code_url'], "base64encodedqrcode")
        self.assertEqual(response_data['status'], "pending")

        # Verify that a new instance was created in the database
        self.assertTrue(WaapiInstance.objects.filter(
            user_profile=self.user_profile,
            instance_id='new-instance-id'
        ).exists())

    @patch('engage.views.waapi_request')
    def test_get_qr_code_failure(self, mock_waapi_request):
        # Mock an error response
        mock_waapi_request.return_value = {
            "qrCode": {
                "status": "error",
                "message": "Failed to generate QR code"
            }
        }

        # Test the API endpoint
        response = self.api_client.get(reverse('get_qr_code'))

        # Check that the response contains the expected data
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIsNone(response_data['qr_code_url'])
        self.assertEqual(response_data['status'], "error")


class CheckWaapiStatusTestCase(EngageViewsTestCase):
    @patch('engage.views.waapi_request')
    def test_check_waapi_status_success(self, mock_waapi_request):
        # Mock the API response for checking status
        mock_waapi_request.return_value = {
            "status": "connected"
        }

        # Test the API endpoint
        response = self.api_client.get(reverse('check_waapi_status'))

        # Check that the response contains the expected data
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], "connected")

        # Verify that waapi_request was called correctly
        mock_waapi_request.assert_called_once_with(
            f"instances/{self.waapi_instance.instance_id}/client/status")

    @patch('engage.views.UserProfile.objects.get')
    def test_check_waapi_status_no_instance(self, mock_get_profile):
        # Set up the mock to return a UserProfile without a WaapiInstance
        profile_mock = MagicMock()
        profile_mock.waapi_instance = None
        mock_get_profile.return_value = profile_mock

        # Test the API endpoint
        response = self.api_client.get(reverse('check_waapi_status'))

        # Check that the response contains the expected error
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'],
                         "No WaAPI instance found for this user.")

    # @patch('engage.views.waapi_request')
    # @patch('engage.views.UserProfile.objects.get')
    # def test_check_waapi_status_request_exception(self, mock_get_profile, mock_waapi_request):
    #     from engage.views import check_waapi_status
        
    #     # Set up request mock
    #     request = self.api_client.get(reverse('check_waapi_status'))
        
    #     # Set up UserProfile mock
    #     profile_mock = MagicMock()
    #     profile_mock.waapi_instance = self.waapi_instance
    #     mock_get_profile.return_value = profile_mock
        
    #     # Mock a request exception
    #     mock_waapi_request.side_effect = Exception("Connection error")
        
    #     # Test the function directly
    #     response = check_waapi_status(request)
        
    #     # Check that the response contains the expected error
    #     self.assertEqual(response.status_code, 500)
    #     response_data = json.loads(response.content)
    #     self.assertEqual(response_data['error'], "Connection error")


class WaapiWebhookTestCase(EngageViewsTestCase):
    def test_waapi_webhook_success(self):
        # Create a sample webhook payload
        payload = {
            "event": "message",
            "data": {
                "message_id": "123456",
                "text": "Hello, world!"
            }
        }

        # Test the API endpoint
        response = self.api_client.post(
            reverse('waapi_webhook'),
            data=json.dumps(payload),
            content_type='application/json'
        )

        # Check that the response indicates success
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], "success")

    def test_waapi_webhook_invalid_json(self):
        # Test the API endpoint with invalid JSON
        response = self.api_client.post(
            reverse('waapi_webhook'),
            data="not valid json",
            content_type='application/json'
        )

        # Check that the response contains the expected error
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], "Invalid JSON")

    def test_waapi_webhook_invalid_method(self):
        # Test the API endpoint with a GET request
        response = self.api_client.get(reverse('waapi_webhook'))

        # Check that the response contains the expected error
        self.assertEqual(response.status_code, 405)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], "Invalid request method")


class GetInstanceIdTestCase(EngageViewsTestCase):
    @patch('engage.views.requests.get')
    def test_get_instance_id_success(self, mock_get):
        # Mock the API response for getting instances
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "instances": [
                {
                    "id": "test-instance-id",
                    "name": f"Instance for {self.user.username}"
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test the API endpoint
        response = self.api_client.get(reverse('get_instance_id'))

        # Check that the response contains the expected data
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['instance_id'], "test-instance-id")

    @patch('engage.views.requests.get')
    def test_get_instance_id_not_found(self, mock_get):
        # Mock the API response for getting instances when the user's instance doesn't exist
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "instances": [
                {
                    "id": "other-instance-id",
                    "name": "Instance for other_user"
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test the API endpoint
        response = self.api_client.get(reverse('get_instance_id'))

        # Check that the response contains the expected error
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.content)
        self.assertEqual(
            response_data['error'], "Instance not found for the user. WaapiInstance removed.")

        # Verify that the WaapiInstance was deleted
        self.assertFalse(WaapiInstance.objects.filter(
            user_profile=self.user_profile).exists())

    @patch('engage.views.requests.get')
    def test_get_instance_id_request_exception(self, mock_get):
        # Mock a request exception
        mock_get.side_effect = Exception("Connection error")

        # Test the API endpoint
        response = self.api_client.get(reverse('get_instance_id'))

        # Check that the response contains the expected error
        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], "Connection error")


class DownloadAndConvertToBase64TestCase(EngageViewsTestCase):
    @patch('engage.views.requests.get')
    def test_download_and_convert_success(self, mock_get):
        # Create sample image content
        sample_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00'

        # Mock the API response for downloading media
        mock_response = MagicMock()
        mock_response.content = sample_image
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Expected base64 output
        expected_base64 = base64.b64encode(sample_image).decode('utf-8')

        # Test the API endpoint
        response = self.api_client.post(
            reverse('download_and_convert_to_base64'),
            data={"mediaUrl": "https://example.com/image.png"},
            format='json'
        )

        # Check that the response contains the expected data
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['base64_code'], expected_base64)

        # Verify that the correct URL was requested
        mock_get.assert_called_once_with("https://example.com/image.png")

    def test_download_and_convert_no_url(self):
        # Test the API endpoint without providing a URL
        response = self.api_client.post(
            reverse('download_and_convert_to_base64'),
            data={},
            format='json'
        )

        # Check that the response contains the expected error
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], "No download URL provided.")


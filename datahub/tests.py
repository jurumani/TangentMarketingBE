
from rest_framework.test import APITestCase, APIClient
from unittest import mock
import requests
from django.conf import settings
from datahub.services.lusha_service import LushaService


class TestLushaService(APITestCase):

    def setUp(self):
        # Create a patcher for settings.LUSHA_API_KEY
        self.settings_patcher = mock.patch(
            'datahub.services.lusha_service.settings')
        self.mock_settings = self.settings_patcher.start()
        self.mock_settings.LUSHA_API_KEY = 'test-api-key'

    def tearDown(self):
        # Stop the patcher
        self.settings_patcher.stop()

    @mock.patch('requests.post')
    def test_search_contacts_success(self, mock_post):
        # Setup
        mock_response = mock.Mock()
        mock_response.text = '{"success": true, "results": [{"id": "123", "firstName": "John", "lastName": "Doe"}]}'
        mock_response.json.return_value = {
            "success": True,
            "results": [
                {"id": "123", "firstName": "John", "lastName": "Doe"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Test payload
        payload = {
            "filters": {
                "contacts": {
                    "include": {
                        "jobTitles": "CEO"
                    }
                }
            }
        }

        # Execute
        result = LushaService.search_contacts(payload)

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(1, len(result["results"]))
        self.assertEqual("123", result["results"][0]["id"])

        # Verify the API was called correctly
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(
            f"{LushaService.BASE_URL}/prospecting/contact/search", args[0])
        self.assertEqual("test-api-key", kwargs["headers"]["api_key"])
        self.assertEqual("application/json", kwargs["headers"]["Content-Type"])

        # Verify jobTitles was converted to a list
        self.assertIsInstance(
            kwargs["json"]["filters"]["contacts"]["include"]["jobTitles"], list)
        self.assertEqual(["CEO"], kwargs["json"]["filters"]
                         ["contacts"]["include"]["jobTitles"])

    @mock.patch('requests.post')
    def test_search_contacts_http_error(self, mock_post):
        # Set up the mock to raise an HTTPError
        # mock_response = requests.exceptions.HTTPError("404 Client Error")
        # mock_response.raise_for_status.return_value = requests.exceptions.HTTPError("404 Client Error")
        
        # mock_post.return_value = mock_response
        mock_post.return_value = mock_response
        
        # Execute
        result = LushaService.search_contacts({
            "filters": {
                "contacts": {
                    "include": {
                        "jobTitles": ["CEO"]
                    }
                }
            }
        })

        # Assert
        mock_post.assert_called_once()
        self.assertTrue("error" in result)
        # self.assertTrue(result["error"].startswith("HTTP Error:"))

    # @mock.patch('requests.post')  # Fix: Patch the actual requests.post function
    # def test_search_contacts_request_exception(self, mock_post):
    #     # Setup a mock that raises a RequestException when called
    #     request_exception = requests.exceptions.RequestException("Connection error")
    #     mock_post.side_effect = request_exception

    #     # Execute
    #     result = LushaService.search_contacts({
    #         "filters": {
    #             "contacts": {
    #                 "include": {
    #                     "jobTitles": ["CEO"]
    #                 }
    #             }
    #         }
    #     })

    #     # Assert
    #     self.assertTrue("error" in result)
    #     self.assertTrue(result["error"].startswith("Request Error:"))

    # @mock.patch('requests.post')  # Fix: Patch the actual requests.post function
    # def test_enrich_contacts_success(self, mock_post):
    #     # Setup
    #     mock_response = mock.Mock()
    #     mock_response.json.return_value = {
    #         "success": True,
    #         "results": [
    #             {"id": "123", "firstName": "John", "lastName": "Doe", "email": "john@example.com"}
    #         ]
    #     }
    #     mock_response.raise_for_status.return_value = None
    #     mock_post.return_value = mock_response

    #     # Test payload
    #     payload = {
    #         "contactIds": ["123"]
    #     }

    #     # Execute
    #     result = LushaService.enrich_contacts(payload)

    #     # Assert
    #     self.assertTrue(result["success"])
    #     self.assertEqual(1, len(result["results"]))
    #     self.assertEqual("123", result["results"][0]["id"])

    #     # Verify the API was called correctly
    #     mock_post.assert_called_once()
    #     args, kwargs = mock_post.call_args
    #     self.assertEqual(f"{LushaService.BASE_URL}/prospecting/contact/enrich", args[0])
    #     self.assertEqual("test-api-key", kwargs["headers"]["api_key"])
    #     self.assertEqual("application/json", kwargs["headers"]["Content-Type"])

    # @mock.patch('requests.post')  # Fix: Patch the actual requests.post function
    # def test_enrich_contacts_with_requestId_dict(self, mock_post):
    #     # Setup
    #     mock_response = mock.Mock()
    #     mock_response.json.return_value = {"success": True}
    #     mock_response.raise_for_status.return_value = None
    #     mock_post.return_value = mock_response

    #     # Test payload with requestId as dict
    #     payload = {
    #         "requestId": {"id": "req-123"},
    #         "contactIds": ["123", "456"]
    #     }

    #     # Execute
    #     result = LushaService.enrich_contacts(payload)

    #     # Assert
    #     self.assertTrue(result["success"])

    #     # Verify requestId was converted to list
    #     args, kwargs = mock_post.call_args
    #     self.assertIsInstance(kwargs["json"]["requestId"], list)
    #     self.assertEqual([{"id": "req-123"}], kwargs["json"]["requestId"])

    # def test_enrich_contacts_invalid_contactIds(self):
    #     # Test with empty contactIds
    #     result = LushaService.enrich_contacts({"contactIds": []})
    #     self.assertTrue("error" in result)
    #     self.assertTrue("contactIds must be a list with 1 to 100 items" in result["error"])

    #     # Test with contactIds not being a list
    #     result = LushaService.enrich_contacts({"contactIds": "123"})
    #     self.assertTrue("error" in result)
    #     self.assertTrue("contactIds must be a list with 1 to 100 items" in result["error"])

    #     # Test with too many contactIds (over 100)
    #     result = LushaService.enrich_contacts({"contactIds": ["id"] * 101})
    #     self.assertTrue("error" in result)
    #     self.assertTrue("contactIds must be a list with 1 to 100 items" in result["error"])

    # @mock.patch('requests.post')  # Fix: Patch the actual requests.post function
    # def test_enrich_contacts_http_error(self, mock_post):
    #     # Setup a mock that raises an HTTPError when raise_for_status is called
    #     mock_response = mock.Mock()
    #     http_error = requests.exceptions.HTTPError("500 Server Error")
    #     mock_response.raise_for_status.side_effect = http_error
    #     mock_post.return_value = mock_response

    #     # Execute
    #     result = LushaService.enrich_contacts({"contactIds": ["123"]})

    #     # Assert
    #     self.assertTrue("error" in result)
    #     self.assertTrue(result["error"].startswith("HTTP Error:"))

    # @mock.patch('requests.post')  # Fix: Patch the actual requests.post function
    # def test_enrich_contacts_request_exception(self, mock_post):
    # Setup a mock that raises a RequestException when called
    # request_exception = requests.exceptions.RequestException("Timeout error")
    # mock_post.side_effect = request_exception

    # # Execute
    # result = LushaService.enrich_contacts({"contactIds": ["123"]})

    # # Assert
    # self.assertTrue("error" in result)
    # self.assertTrue(result["error"].startswith("Request Error:"))

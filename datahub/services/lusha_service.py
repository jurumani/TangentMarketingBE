# services/lusha_service.py
import requests
from django.conf import settings
import traceback


class LushaService:
    BASE_URL = "https://api.lusha.com"

    @staticmethod
    def search_contacts(payload):
        headers = {
            "api_key": settings.LUSHA_API_KEY,
            "Content-Type": "application/json"
        }

        url = f"{LushaService.BASE_URL}/prospecting/contact/search"

        # ✅ Ensure jobTitles is always a list
        if isinstance(payload["filters"]["contacts"]["include"].get("jobTitles"), str):
            payload["filters"]["contacts"]["include"]["jobTitles"] = [
                payload["filters"]["contacts"]["include"]["jobTitles"]
            ]

        print(f"🔍 DEBUG: Making request to Lusha API: {url}")
        print(f"🔍 DEBUG: Headers sent: {headers}")
        # Ensure correct payload format
        print(f"🔍 DEBUG: Payload sent: {payload}")

        try:
            response = requests.post(url, json=payload, headers=headers)
            print(f"🔍 DEBUG: Raw Response: {response.text}")
            response.raise_for_status()

            response_data = response.json()
            print(f"✅ Lusha response: {response_data}")

            return response_data

        except requests.exceptions.HTTPError as e:
            print(f"❌ Lusha API HTTP error: {e}")
            traceback.print_exc()
            return {"error": f"HTTP Error: {str(e)}"}

        except requests.exceptions.RequestException as e:
            print(f"❌ Lusha API request error: {e}")
            traceback.print_exc()
            return {"error": f"Request Error: {str(e)}"}

    @staticmethod
    def enrich_contacts(payload):
        headers = {
            "api_key": settings.LUSHA_API_KEY,
            "Content-Type": "application/json"
        }
        url = f"{LushaService.BASE_URL}/prospecting/contact/enrich"

        # Validate requestId
        if isinstance(payload.get("requestId"), dict):
            payload["requestId"] = [payload["requestId"]]

        # Validate contactIds
        contact_ids = payload.get("contactIds")
        if not isinstance(contact_ids, list) or not (1 <= len(contact_ids) <= 100):
            return {"error": "contactIds must be a list with 1 to 100 items"}

        print(f"🔍 DEBUG: Making request to Lusha API: {url}")
        print(f"🔍 DEBUG: Headers sent: {headers}")
        print(f"🔍 DEBUG: Payload sent: {payload}")

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            response_data = response.json()
            print(f"✅ Lusha response: {response_data}")

            return response_data

        except requests.exceptions.HTTPError as e:
            print(f"❌ Lusha API HTTP error: {e}")
            traceback.print_exc()
            return {"error": f"HTTP Error: {str(e)}"}

        except requests.exceptions.RequestException as e:
            print(f"❌ Lusha API request error: {e}")
            traceback.print_exc()
            return {"error": f"Request Error: {str(e)}"}

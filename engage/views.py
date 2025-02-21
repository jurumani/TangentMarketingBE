# engage/views.py
from django.http import JsonResponse
from django.conf import settings
import requests
from django.utils import timezone
from .models import WaapiInstance
from django.contrib.auth.decorators import login_required
from users.models import UserProfile  # Assuming UserProfile is where the link to WaapiInstance is stored
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

# Ensure you have WAAPI_BASE_URL and API_KEY in your Django settings
WAAPI_BASE_URL = settings.WAAPI_BASE_URL
print (WAAPI_BASE_URL)
API_KEY = settings.WAAPI_API_KEY

# View to create a new instance for a user if one doesn't exist
def create_or_get_instance(request):
    user = request.user
    
    # Check if the user already has an instance
    try:
        instance = WaapiInstance.objects.get(user=user)
    except WaapiInstance.DoesNotExist:
        # If no instance exists, create one through the WaAPI API
        url = f"{WAAPI_BASE_URL}/instances"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        data = {"name": f"Instance for {user.username}"}

        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        response_data = response.json()

        # Save the new instance to the database
        instance = WaapiInstance.objects.create(
            user=user,
            instance_id=response_data["id"],
            is_linked=False,
        )

    return JsonResponse({
        "instance_id": instance.instance_id,
        "is_linked": instance.is_linked
    })

# Helper function to make requests to WaAPI with authentication headers
import json

def waapi_request(endpoint, method="GET", data=None):
    """Helper function to make requests to WaAPI with authentication headers."""
    headers = {
        "Authorization": f"Bearer {settings.WAAPI_API_KEY}",  # Ensure API key is correct
        "Content-Type": "application/json",
    }
    url = f"{settings.WAAPI_BASE_URL}/{endpoint}"

    print(f"Making {method} request to {url}")
    print(f"Headers: {headers}")
    if data:
        print(f"Payload: {json.dumps(data, indent=2)}")

    try:
        if method == "POST":
            response = requests.post(url, json=data, headers=headers)
        else:
            response = requests.get(url, headers=headers)

        # Debugging: Print response status & content
        print(f"Response Status: {response.status_code}")
        print(f"Response Content: {response.text}")

        # Raise error if response is unsuccessful
        response.raise_for_status()

        # Handle potential empty response
        if not response.text:
            print("⚠️ Warning: Received empty response from WaAPI")
            return {}

        return response.json()

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP Error: {http_err}")
        return {"error": f"HTTP Error: {http_err}"}
    
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection Error: {conn_err}")
        return {"error": f"Connection Error: {conn_err}"}
    
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout Error: {timeout_err}")
        return {"error": f"Timeout Error: {timeout_err}"}
    
    except requests.exceptions.RequestException as req_err:
        print(f"Request Error: {req_err}")
        return {"error": f"Request Error: {req_err}"}
    
    except json.decoder.JSONDecodeError as json_err:
        print(f"JSON Decode Error: {json_err}")
        return {"error": "Invalid JSON response from WaAPI"}




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_qr_code(request):
    try:
        # ✅ 1. Ensure user is authenticated
        user = request.user
        print(f"Authenticated user: {user.username}")  # Debugging line

        # ✅ 2. Fetch UserProfile
        try:
            user_profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return JsonResponse({"error": "User profile not found."}, status=404)

        # ✅ 3. Check if WaapiInstance exists for the user
        waapi_instance = WaapiInstance.objects.filter(user_profile=user_profile).first()

        if not waapi_instance:
            print(f"Creating new WaapiInstance for {user.username}...")

            # ✅ 4. Create a new instance in WaAPI
            instance_payload = {"name": f"{user.username}'s Instance"}
            create_instance_response = waapi_request("instances", method="POST", data=instance_payload)

            # ✅ 5. Debug: Print response from WaAPI
            print(f"Response from WaAPI instance creation: {create_instance_response}")

            # ✅ 6. Check if the instance was created successfully
            # ✅ 6. Check if the instance was created successfully
            if not create_instance_response or "instance" not in create_instance_response or "id" not in create_instance_response["instance"]:
                return JsonResponse({"error": "Failed to create instance in WaAPI"}, status=500)

            instance_id = create_instance_response["instance"]["id"]  # ✅ Correctly extract instance ID

            if not instance_id:
                return JsonResponse({"error": "Instance ID missing in WaAPI response"}, status=500)

            # ✅ 7. Save the new instance in our DB
            waapi_instance = WaapiInstance.objects.create(
                user_profile=user_profile,
                instance_id=instance_id,
                status="qr"
            )

            print(f"✅ Successfully created new WaapiInstance with ID {instance_id}")

        # ✅ 8. Debug: Ensure instance_id is valid before requesting QR code
        if not waapi_instance.instance_id:
            return JsonResponse({"error": "Instance ID is empty, cannot fetch QR code."}, status=500)

        print(f"Fetching QR code for WaAPI Instance ID: {waapi_instance.instance_id}")

        # ✅ 9. Request the QR code for this instance
        endpoint = f"instances/{waapi_instance.instance_id}/client/qr"
        qr_code_data = waapi_request(endpoint)

        # ✅ 10. Debug: Print QR code response
        print(f"QR Code Response: {qr_code_data}")

        if not qr_code_data:
            return JsonResponse({"error": "Failed to retrieve QR code from WaAPI."}, status=500)

        # ✅ 11. Check if QR code is available
        if qr_code_data.get("qrCode", {}).get("status") == "success":
            qr_code_base64 = qr_code_data["qrCode"]["data"]["qr_code"]
            return JsonResponse({"qr_code_url": qr_code_base64, "status": "pending"})

        # Handle case when the instance is not in QR mode or another issue occurs
        return JsonResponse({"qr_code_url": None, "status": qr_code_data["qrCode"]["status"]})

    except requests.RequestException as e:
        print(f"RequestException in get_qr_code: {e}")
        return JsonResponse({"error": str(e)}, status=500)

# View to check the connection status of a user's WaapiInstance

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_waapi_status(request):
    user_profile = UserProfile.objects.get(user=request.user)

    try:
        waapi_instance = user_profile.waapi_instance
        if not waapi_instance:
            return JsonResponse({"error": "No WaAPI instance found for this user."}, status=404)

        endpoint = f"instances/{waapi_instance.instance_id}/client/status"
        status_data = waapi_request(endpoint)
        
        return JsonResponse({"status": status_data.get("status")})

    except requests.RequestException as e:
        print(f"Error during WaAPI status request: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@permission_classes([IsAuthenticated])
def waapi_webhook(request):
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            # Process the webhook payload here
            # Example: Log the event or update a database record
            print("Received Waapi webhook:", payload)

            # Respond with a 200 OK status to acknowledge receipt
            return JsonResponse({'status': 'success'})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
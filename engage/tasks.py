import base64
import json
import logging
from celery import shared_task
from django.conf import settings
import requests
from core.settings import SYNTHESIA_API_KEY
from engage.models import SynthesiaVideo
from engage.utils import render_message_template
from datetime import datetime as dt, timedelta
import pytz  # Add this import

from users.models import User



logger = logging.getLogger(__name__)


@shared_task
def create_synthesia_video(video_id, user_id):
    """
    Task to create a video in Synthesia.

    Args:
        video_id: The ID of the SynthesiaVideo object
    """
    try:
        # Get the video object
        video = SynthesiaVideo.objects.get(id=video_id)

        # Skip if already processed
        if video.synthesia_id:
            logger.info(
                f"Video {video_id} already has Synthesia ID: {video.synthesia_id}")
            return

        # Get the API key from settings
        api_key = getattr(settings, 'SYNTHESIA_API_KEY', None)
        if not api_key:
            raise Exception("SYNTHESIA_API_KEY not configured in settings")

        # Get API endpoint from settings or use default
        api_endpoint = getattr(
            settings, 'SYNTHESIA_API_ENDPOINT', 'https://api.synthesia.io/v2/videos')

        # Prepare headers
        headers = {
            'Authorization': f'{api_key}',
            'Content-Type': 'application/json'
        }

        # Get payload data from model
        payload = video.get_synthesia_payload()

        # Make API request
        response = requests.post(
            api_endpoint,
            headers=headers,
            data=json.dumps(payload)
        )

        # Check for successful response
        response.raise_for_status()

        # Update model with response data
        video.update_from_synthesia_response(response.json())

        logger.info(
            f"Successfully created Synthesia video with ID: {video.synthesia_id}")

        # Schedule task to check video status
        check_synthesia_video_status.apply_async(
            args=[video_id, user_id],
            countdown=60  # Check after 1 minute
        )

    except SynthesiaVideo.DoesNotExist:
        logger.error(f"SynthesiaVideo with ID {video_id} not found")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating Synthesia video: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response content: {e.response.content}")

            # Update video with error message
            video = SynthesiaVideo.objects.get(id=video_id)
            video.status = 'failed'
            video.error_message = f"API Error: {e.response.content}"
            video.save()
    except Exception as e:
        logger.error(f"Unexpected error creating Synthesia video: {str(e)}")


@shared_task
def check_synthesia_video_status(video_id, user_id):
    """
    Task to check the status of a Synthesia video.

    Args:
        video_id: The ID of the SynthesiaVideo object
    """
    try:
        # Get the video object
        video = SynthesiaVideo.objects.get(id=video_id)

        # Skip if no Synthesia ID
        if not video.synthesia_id:
            logger.error(f"Video {video_id} has no Synthesia ID to check")
            return

        # Get the API key from settings
        api_key = getattr(settings, 'SYNTHESIA_API_KEY', None)
        if not api_key:
            raise Exception("SYNTHESIA_API_KEY not configured in settings")

        # Get API endpoint from settings or use default
        api_endpoint = f"https://api.synthesia.io/v2/videos/{video.synthesia_id}"

        # Prepare headers
        headers = {
            'Authorization': f'{api_key}',
            'Content-Type': 'application/json'
        }

        # Make API request
        response = requests.get(
            api_endpoint,
            headers=headers
        )

        # Check for successful response
        response.raise_for_status()

        # Update model with response data
        response_data = response.json()
        logger.debug(
            f"Synthesia video {video.synthesia_id} response: {response_data}")
        video.update_from_synthesia_response(response_data)

        logger.info(
            f"Synthesia video {video.synthesia_id} status: {video.status}")

        # If video is not yet complete or failed, schedule another check
        if video.status not in ['complete', 'failed']:
            # Check again after 3 minutes
            check_synthesia_video_status.apply_async(
                args=[video_id, user_id],
                countdown=180
            )
        elif video.status == 'complete' and video.is_ready_for_whatsapp:
            # If video is complete and marked for WhatsApp sending, trigger that task
            send_synthesia_video_via_whatsapp.apply_async(
                args=[video_id, user_id]
            )

    except SynthesiaVideo.DoesNotExist:
        logger.error(f"SynthesiaVideo with ID {video_id} not found")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking Synthesia video status: {str(e)}")

    except Exception as e:
        logger.error(
            f"Unexpected error checking Synthesia video status: {str(e)}")


@shared_task
def send_synthesia_video_via_whatsapp(video_id, user_id):
    """
    Task to send a completed Synthesia video via WhatsApp.

    Args:
        video_id: The ID of the SynthesiaVideo object
    """
    try:
        # Get the video object
        video = SynthesiaVideo.objects.get(id=video_id)

        # Skip if no download URL
        if not video.download_url:
            logger.error(f"Video {video_id} has no download URL")
            return

        # Set timezone to South Africa/Johannesburg
        tz = pytz.timezone('Africa/Johannesburg')
        current_time = dt.now(tz).time()
        start_time = dt.strptime("08:00", "%H:%M").time()
        end_time = dt.strptime("17:00", "%H:%M").time()
        early_morning_end_time = dt.strptime("07:00", "%H:%M").time()

        if not (start_time <= current_time <= end_time):
            video.status = 'pending'
            video.error_message = 'WhatsApp messages can only be sent between 08:00 and 17:00.'
            video.save()
            logger.info(f"Video {video_id} scheduled to send WhatsApp message between 08:00 and 17:00")

            # Schedule the task to run at 08:00 on the current day if time is between 00:00 and 07:00
            if current_time <= early_morning_end_time:
                next_run_time = dt.combine(dt.now(tz), start_time)
            else:
                # Schedule the task to run the following day at 08:00
                next_run_time = dt.combine(dt.now(tz) + timedelta(days=1), start_time)
                
            send_synthesia_video_via_whatsapp.apply_async(args=[video_id, user_id], eta=next_run_time)
            return

        # Get the instance ID
        user = User.objects.get(id=user_id)
        url = f"{settings.WAAPI_BASE_URL}/instances"
        headers = {"Authorization": f"Bearer {settings.WAAPI_API_KEY}", "accept": "application/json"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        instances = response_data.get("instances", [])
        user_instance = next((instance for instance in instances if user.username in instance["name"]), None)

        if not user_instance:
            logger.error(f"Instance not found for user {user.username}")
            return

        instance_id = user_instance["id"]

        # Download the media from the URL
        response = requests.get(video.download_url)
        response.raise_for_status()

        # Convert the media content to base64
        media_content = response.content
        base64_encoded = base64.b64encode(media_content).decode('utf-8')

        # Send the media to WAAPI
        waapi_url = f"{settings.WAAPI_BASE_URL}/instances/{instance_id}/client/action/send-media"
        waapi_headers = {
            "Authorization": f"Bearer {settings.WAAPI_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        waapi_data = {
            "mediaName": f"{video.title}.mp4",
            "chatId": f"{video.whatsapp_number}@c.us",
            "mediaCaption": f"*_Video Title: {video.title}_*\n\nDescription: {video.description}\n",
            "mediaBase64": base64_encoded
        }

        waapi_response = requests.post(waapi_url, json=waapi_data, headers=waapi_headers)
        waapi_response.raise_for_status()
        

        # Mark video as sent
        video.mark_as_sent()

        logger.info(
            f"Sent Synthesia video {video.synthesia_id} via WhatsApp to {video.whatsapp_number}")

    except SynthesiaVideo.DoesNotExist:
        logger.error(f"SynthesiaVideo with ID {video_id} not found")
    except requests.RequestException as e:
        logger.error(f"RequestException in send_synthesia_video_via_whatsapp: {e}")
    except Exception as e:
        logger.error(f"Error sending Synthesia video via WhatsApp: {str(e)}")


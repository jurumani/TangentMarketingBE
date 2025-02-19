from celery import shared_task
from engage.models import CampaignMessage, CampaignContact
from engage.utils import render_message_template
from twilio.rest import Client

@shared_task
def send_whatsapp_message(campaign_message_id, campaign_contact_id):
    campaign_message = CampaignMessage.objects.get(id=campaign_message_id)
    campaign_contact = CampaignContact.objects.get(id=campaign_contact_id)
    contact = campaign_contact.contact

    # Render the message template with contact and company details
    message_body = render_message_template(campaign_message.template, contact)

    # Twilio client setup (ensure TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are in environment)
    client = Client("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN")
    from_whatsapp_number = 'whatsapp:+14155238886'  # Twilio WhatsApp sandbox number
    to_whatsapp_number = f'whatsapp:{contact.mobile}'

    # Send WhatsApp message
    message = client.messages.create(
        body=message_body,
        from_=from_whatsapp_number,
        to=to_whatsapp_number,
        media_url=[campaign_message.media_url] if campaign_message.media_url else None
    )

    # Update CampaignContact status
    campaign_contact.status = "sent" if message.sid else "failed"
    campaign_contact.save()

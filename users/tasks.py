from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_welcome_email(user_email):
    """
    A simple task to send a welcome email to a newly registered user.
    """
    subject = 'Welcome to My Project'
    message = 'Thanks for signing up for our platform!'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [user_email]
    
    send_mail(subject, message, email_from, recipient_list)
    return f"Email sent to {user_email}"

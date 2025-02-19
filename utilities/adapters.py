from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.core.mail import send_mail

class CustomAccountAdapter(DefaultAccountAdapter):

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        # Construct the email confirmation URL for Vue frontend
        confirm_url = f"{settings.FRONTEND_URL}/verify-email/{emailconfirmation.key}/"

        # Email subject and message
        subject = f"Confirm your email address for {settings.SITE_NAME}"
        message = f"""
        Hello {emailconfirmation.email_address.user},

        You're receiving this email because a user account was registered on {settings.SITE_NAME} with your email address.

        To confirm your account, please click the following link:
        {confirm_url}

        If you did not register on our site, please ignore this email.

        Thank you for using {settings.SITE_NAME}!
        """
        # Send the email
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [emailconfirmation.email_address.email], fail_silently=False)

    def send_mail(self, template_prefix, email, context):
        # Check if the email is for a password reset
        if template_prefix == 'account/email/password_reset_key':
            # Construct the password reset URL for Vue frontend
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{context['key']}/"
            context['password_reset_url'] = reset_url

        # Call the default send_mail to handle the email sending
        super().send_mail(template_prefix, email, context)

    def get_password_reset_redirect_url(self, request):
        # Redirect to the frontend login page after password reset
        return f"{settings.FRONTEND_URL}/login"

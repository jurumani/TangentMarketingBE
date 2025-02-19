from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import ensure_csrf_cookie
from allauth.account.models import EmailConfirmationHMAC
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({'detail': 'CSRF cookie set'})

@api_view(['POST'])
@permission_classes([AllowAny])  # Make sure this is applied correctly
def verify_email(request):
    try:
        # Extract the key from the request data
        key = request.data.get('key')

        # Use the key to retrieve the email confirmation object
        email_confirmation = EmailConfirmationHMAC.from_key(key)
        if email_confirmation:
            # Confirm the email
            email_confirmation.confirm(request)
            # Return success response
            return Response({'detail': 'Email confirmed successfully'}, status=status.HTTP_200_OK)
        else:
            # Invalid confirmation key
            return Response({'detail': 'Invalid confirmation key'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        # Return any error that occurred during the process
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

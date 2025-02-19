from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .serializers import UserSerializer, GroupSerializer, UserProfileSerializer, PublicUserSerializer
from .models import UserProfile
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q
from rest_framework.views import APIView
from allauth.account.views import LoginView as AllauthLoginView
from allauth.account.views import LogoutView as AllauthLogoutView
from allauth.account.models import EmailAddress
from rest_framework import status
from allauth.account.utils import complete_signup
from allauth.account.adapter import get_adapter
from allauth.account import app_settings as allauth_settings
from django.conf import settings
from allauth.account.forms import SignupForm
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from allauth.account.models import EmailAddress
from django.conf import settings
from allauth.account import app_settings as allauth_settings
from rest_framework.permissions import AllowAny


from rest_framework import status
from allauth.account.forms import SignupForm, LoginForm
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from allauth.account.utils import complete_signup
from rest_framework.permissions import AllowAny
from allauth.account.utils import send_email_confirmation

from allauth.account.views import PasswordResetView
from allauth.account.views import PasswordResetFromKeyView

from django.urls import reverse




User = get_user_model()

class UsersViewSet(viewsets.ViewSet):
    """
    A ViewSet for managing user-related actions such as login, logout, listing users, deleting users,
    and managing user groups. Provides endpoints for handling user authentication and group management.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username for login'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email for login'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password for login')
            },
            required=['username', 'password'],
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'token': openapi.Schema(type=openapi.TYPE_STRING, description='Authentication token'),
                    'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
                    'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email'),
                }
            ),
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                }
            ),
        },
        operation_summary="Login a User",
        operation_description="Authenticate a user using their username/email and password.",
    )
    @action(detail=False, methods=['post'], permission_classes=[])
    def login(self, request):
        view = AllauthLoginView.as_view()  # Use Allauth Login View
        return view(request._request)

    @swagger_auto_schema(
        method='post',
        responses={204: 'Logout successful'},
        operation_summary="Logout a User",
        operation_description="Log out a user.",
    )
    @action(detail=False, methods=['post'])
    def logout(self, request):
        view = AllauthLogoutView.as_view()  # Use Allauth Logout View
        return view(request._request)

    @swagger_auto_schema(
        method='get',
        responses={200: UserSerializer(many=True)},
        operation_summary="List All Users",
        operation_description="Retrieve a list of all users. Restricted to admin users.",
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def list_users(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        method='get',
        responses={200: PublicUserSerializer(many=True)},
        operation_summary="Search for Users",
        operation_description="Search for users by username, first name, or last name. Restricted to authenticated users.",
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def search_users(self, request):
        search_query = request.query_params.get('search', '')

        if search_query:
            users = User.objects.filter(
                Q(username__icontains=search_query) | 
                Q(first_name__icontains=search_query) | 
                Q(last_name__icontains=search_query)
            )[:10]  # Limit results to 10
        else:
            return Response({'detail': 'Search query missing'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PublicUserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        method='delete',
        responses={204: 'User deleted', 404: 'User not found'},
        operation_summary="Delete a User by ID",
        operation_description="Delete a user by their ID. Restricted to admin users.",
    )
    @action(detail=True, methods=['delete'], permission_classes=[IsAdminUser])
    def delete_user(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        method='get',
        responses={200: GroupSerializer(many=True)},
        operation_summary="List All Groups",
        operation_description="Retrieve a list of all groups. Restricted to admin users.",
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def list_groups(self, request):
        groups = Group.objects.all()
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        method='post',
        request_body=GroupSerializer,
        responses={201: GroupSerializer},
        operation_summary="Create a New Group",
        operation_description="Create a new user group. Restricted to admin users.",
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def create_group(self, request):
        serializer = GroupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        method='delete',
        responses={204: 'Group deleted', 404: 'Group not found'},
        operation_summary="Delete a Group by ID",
        operation_description="Delete a group by its ID. Restricted to admin users.",
    )
    @action(detail=True, methods=['delete'], permission_classes=[IsAdminUser])
    def delete_group(self, request, pk=None):
        try:
            group = Group.objects.get(pk=pk)
            group.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Group.DoesNotExist:
            return Response({"detail": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

    # User Profile Update Endpoint
    @swagger_auto_schema(
        method='put',
        request_body=UserProfileSerializer,
        responses={200: UserProfileSerializer},
        operation_summary="Update User Profile",
        operation_description="Update the user's profile information."
    )
    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        user = request.user
        profile = user.profile  # Get the associated UserProfile
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        method='get',
        responses={200: UserProfileSerializer},
        operation_summary="Get User Profile",
        operation_description="Retrieve the profile information for the logged-in user."
    )
    @action(detail=False, methods=['get'])
    def profile(self, request):
        user = request.user
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'old_password': openapi.Schema(type=openapi.TYPE_STRING, description='Old password'),
                'new_password1': openapi.Schema(type=openapi.TYPE_STRING, description='New password'),
                'new_password2': openapi.Schema(type=openapi.TYPE_STRING, description='Confirm new password'),
            },
            required=['old_password', 'new_password1', 'new_password2'],
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Password changed successfully'),
                }
            ),
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message'),
                }
            ),
        },
        operation_summary="Change User Password",
        operation_description="Change the user's password. Requires the old password and new password.",
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        user = request.user
        form = PasswordChangeForm(user=user, data=request.data)
        
        if form.is_valid():
            # Save the new password using form's save method
            user = form.save()
            update_session_auth_hash(request, user)  # Update the session with the new password
            return Response({'detail': 'Password changed successfully'}, status=status.HTTP_200_OK)
        else:
            # Return form errors if password change fails
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomSignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Process the data using the allauth SignupForm
        form = SignupForm(data=request.data)
        
        if form.is_valid():
            user = form.save(request)
            
            # Manually handle first_name and last_name from request data
            user.first_name = request.data.get('first_name', '')
            user.last_name = request.data.get('last_name', '')
            user.save()  # Save the user with the updated first and last names
            
            # Send email confirmation manually
            send_email_confirmation(request, user)
            return Response({'detail': 'Registration successful. Please check your email for verification.'}, status=status.HTTP_201_CREATED)
        else:
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'detail': 'Login successful', 'token': token.key}, status=status.HTTP_200_OK)
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

class CustomLogoutView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user must be authenticated to logout

    def post(self, request):
        token = request.auth
        if token:
            token.delete()  # Delete the token to log the user out
            return Response({'detail': 'Logout successful'}, status=status.HTTP_200_OK)
        return Response({'detail': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

#//FIXME: All Password Reset Views are not working and need to be resolved.CustomPasswordResetView, CustomPasswordResetConfirmView, CustomPasswordResetFromKeyView
class CustomPasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Use Allauth's PasswordResetView logic to initiate the reset process
        view = PasswordResetView.as_view()
        return view(request._request)
    
class CustomPasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        key = request.data.get("key")
        password = request.data.get("password")
        
        if not key or not password:
            return Response({'error': 'Key and password are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update the request data to include the reset key
        request.data.update({'key': key, 'password1': password, 'password2': password})
        
        # Delegate to Allauth's PasswordResetFromKeyView to handle the reset
        view = PasswordResetFromKeyView.as_view()
        return view(request._request)

class CustomPasswordResetFromKeyView(PasswordResetFromKeyView):
    def get_context_data(self, **kwargs):
        # Override to redirect to the frontend login URL, not using account_login reverse
        context = super().get_context_data(**kwargs)
        context['login_url'] = f"{settings.FRONTEND_URL}/login"
        return context

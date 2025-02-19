from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Message
from .serializers import MessageSerializer
from rest_framework.decorators import action

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        This ensures that only the messages where the logged-in user is either the recipient or the sender are returned.
        """
        user = self.request.user
        return Message.objects.filter(recipient=user) | Message.objects.filter(sender=user)

    # Swagger query parameters for filtering messages
    sent_param = openapi.Parameter(
        'sent', openapi.IN_QUERY, description="Filter to get only sent messages", type=openapi.TYPE_BOOLEAN
    )
    received_param = openapi.Parameter(
        'received', openapi.IN_QUERY, description="Filter to get only received messages", type=openapi.TYPE_BOOLEAN
    )

    @swagger_auto_schema(
        manual_parameters=[sent_param, received_param],
        operation_id='List User Messages',
        operation_description="Retrieve messages for the logged-in user. Use `sent=true` for sent messages and `received=true` for received messages.",
        responses={200: MessageSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """
        List messages for the logged-in user.
        Use query params to filter sent, received, or unread messages.
        """
        user = request.user
        queryset = Message.objects.all()

        # Filter messages based on query params
        sent = request.query_params.get('sent', None)
        received = request.query_params.get('received', None)
        unread = request.query_params.get('unread', None)

        if sent and sent.lower() == 'true':
            queryset = queryset.filter(sender=user)
        elif received and received.lower() == 'true' or not (sent or received):  # Default to received if no param
            queryset = queryset.filter(recipient=user)

        # Filter unread messages if `unread=true` is passed
        if unread and unread.lower() == 'true':
            queryset = queryset.filter(is_read=False)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)



    @swagger_auto_schema(
        request_body=MessageSerializer,
        operation_id='Create New Message',
        operation_description="Create a new message. If `is_system_message` is true, the sender will be set to null.",
        responses={201: MessageSerializer}
    )
    def create(self, request, *args, **kwargs):
        """
        Create a new message for the logged-in user.
        Automatically sets the sender to the authenticated user unless it's a system message.
        """
        # Make a copy of the request data to modify
        data = request.data.copy()

        # Set the sender to the logged-in user if it's not a system message
        if not data.get('is_system_message', False):
            data['sender'] = request.user.id

        # Create the message with modified data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


    @swagger_auto_schema(
        operation_id='Retrieve User Message',
        operation_description="Retrieve a specific message by its ID.",
        responses={200: MessageSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a message by its ID.
        """
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=MessageSerializer,
        operation_id='Update User Message',
        operation_description="Update a specific message entirely by its ID.",
        responses={200: MessageSerializer}
    )
    def update(self, request, *args, **kwargs):
        """
        Update a message by its ID.
        """
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=MessageSerializer,
        operation_id='Partially Update User Message',
        operation_description="Partially update a specific message by its ID.",
        responses={200: MessageSerializer}
    )
    def partial_update(self, request, *args, **kwargs):
        """
        Partially update a message by its ID.
        """
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id='Delete User Message',
        operation_description="Delete a specific message by its ID.",
        responses={204: 'Message deleted successfully'}
    )
    def destroy(self, request, *args, **kwargs):
        """
        Delete a message by its ID.
        """
        return super().destroy(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_id='Trigger Message Action',
        operation_description="Trigger a specific action for a message, such as accepting or rejecting.",
        responses={200: "Action performed successfully"}
    )
    @action(detail=True, methods=['post'], url_path='trigger-action')
    def trigger_action(self, request, pk=None):
        message = self.get_object()
        action_type = request.data.get('action')

        if not action_type:
            return Response({"detail": "No action specified."}, status=status.HTTP_400_BAD_REQUEST)

        # Perform the action (future developer can customize this)
        message.trigger_action(action_type)

        return Response({"detail": f"Action '{action_type}' performed successfully."}, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_id='Mark Message as Read',
        operation_description="Mark a specific message as read for the logged-in recipient.",
        responses={200: openapi.Response('Message marked as read successfully'),
                   403: openapi.Response('Not authorized to mark this message as read')},
    )
    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_as_read(self, request, pk=None):
        """
        Mark a message as read.
        """
        message = self.get_object()

        # Ensure only the recipient, not the sender, can mark the message as read
        if message.recipient != request.user:
            return Response({'detail': 'Not authorized to mark this message as read'}, status=status.HTTP_403_FORBIDDEN)

        message.is_read = True
        message.save()

        return Response({'detail': 'Message marked as read'}, status=status.HTTP_200_OK)
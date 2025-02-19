import requests
import traceback  # Import traceback to get detailed error messages
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from django.core.files.storage import default_storage
from .tasks import process_uploaded_file
from .models import Contact, Company, Service
from .serializers import ContactSerializer, CompanySerializer, ServiceSerializer
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet
from users.models import UserProfile  # Ensure you import UserProfile
from rest_framework.views import APIView
from .services.lusha_service import LushaService


class DataIngestionViewSet(viewsets.ViewSet):
    """
    A ViewSet for ingesting data files (e.g., Excel) from different sources (e.g., Bitrix, LinkedIn).
    """
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

    @action(detail=False, methods=['post'])
    def ingest_file(self, request):
        data_source = request.headers.get('source')
        data_type = request.headers.get('type')
        visibility = request.headers.get('visibility')

        if not data_source or not data_type:
            return Response({'error': 'Both source and type headers are required.'}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES.get('file')

        if not uploaded_file:
            return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

        file_name = default_storage.save(f"uploads/{uploaded_file.name}", uploaded_file)
        file_path = default_storage.path(file_name)

        # Pass request.user to process_uploaded_file to add the uploader as an owner
        process_uploaded_file.delay(file_path, data_source, data_type, request.user.id, visibility)

        return Response({
            'detail': 'File uploaded successfully and processing started.',
            'file_name': file_name,
            'source': data_source,
            'type': data_type
        }, status=status.HTTP_201_CREATED)

# Custom pagination class
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10  # Items per page
    page_size_query_param = 'page_size'
    max_page_size = 100


# In datahub/views.py
class ContactViewSet(ModelViewSet):
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        user_profile = UserProfile.objects.get(user=user)
        queryset = user_profile.personal_contacts.all()

        # Filter by search query if provided
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email_address__icontains=search_query) |
                Q(company__name__icontains=search_query)
            )

        return queryset

class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        user_profile = UserProfile.objects.get(user=user)
        queryset = user_profile.personal_companies.all().order_by('created_at')

        # Filter by search query if provided
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(address__icontains=search_query)
            )

        # Filter by selected services
        services = self.request.query_params.getlist('services[]')
        print(f"Received services filter: {services}")  # Debugging output
        if services:
            queryset = queryset.filter(domains__services__name__in=services).distinct()
        
        print(f"Final queryset count after filters: {queryset.count()}")  # Debug final filtered count
        return queryset

    # Existing contacts action
    @action(detail=True, methods=['get'], url_path='contacts', url_name='company-contacts')
    def contacts(self, request, pk=None):
        company = self.get_object()
        contacts = Contact.objects.filter(company=company)
        page = self.paginate_queryset(contacts)
        if page is not None:
            serializer = ContactSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)

class ServiceViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for listing or retrieving services.
    """
    @action(detail=False, methods=['get'])
    def list_services(self, request):
        services = Service.objects.all()
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)

class LushaContactSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = request.data
        print(f"Received payload for Lusha API: {payload}")  # Debugging payload received

        try:
            # Call Lusha API
            lusha_response = LushaService.search_contacts(payload)
            print(f"Lusha API response: {lusha_response}")  # Debugging response

            # ✅ Correct the key from 'contacts' to 'data'
            contacts = lusha_response.get('data', [])
            if not contacts:
                print("⚠️ No contacts returned from Lusha API.")
                return Response({'detail': 'No contacts found.'}, status=200)

            for contact in contacts:
                try:
                    # Extract contact details
                    company_name = contact.get("companyName", "Unknown Company")
                    company_website = contact.get("fqdn", "")
                    company_description = contact.get("companyDescription", "").strip()
                    logo_url = contact.get("logoUrl", "")

                    # Extract contact details
                    contact_id = contact.get("contactId", "")
                    first_name = contact["name"].get("first", "")
                    last_name = contact["name"].get("last", "")
                    job_title = contact.get("jobTitle", "")
                    work_email = contact.get("hasWorkEmail", False)
                    mobile_phone = contact.get("hasMobilePhone", False)
                    linkedin_url = contact.get("hasSocialLink", False)

                    # Ensure we only process contacts with valid emails
                    if not work_email:
                        print(f"Skipping contact {first_name} {last_name} (No email found)")
                        continue

                    # Create or update company
                    company, _ = Company.objects.get_or_create(
                        name=company_name,
                        defaults={
                            'address': company_website,
                        }
                    )

                    # Save or update contact details
                    contact_obj, created = Contact.objects.update_or_create(
                        email_address=work_email,
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name,
                            'company': company,
                            'work_phone': mobile_phone,
                            'position': job_title,
                            'linkedin_profile': linkedin_url,
                            'import_source': 'Lusha',
                            'visibility': 'public'
                        }
                    )
                    print(f"✅ Processed contact: {contact_obj}, Created: {created}")

                except Exception as e:
                    print(f"❌ Error processing contact {contact}: {e}")
                    traceback.print_exc()  # Print detailed error traceback

            return Response({'detail': 'Contacts successfully enriched and saved.'})

        except requests.RequestException as e:
            print(f"❌ Error fetching from Lusha API: {e}")
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)

        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)

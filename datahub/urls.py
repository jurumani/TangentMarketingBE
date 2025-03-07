from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DataIngestionViewSet, ContactViewSet, CompanyViewSet, ServiceViewSet, LushaContactSearchView, LushaContactsEnrichView

# Initialize the router
router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'contacts', ContactViewSet, basename='contact')

# Define URL patterns
urlpatterns = [
    path('', include(router.urls)),  # Automatically register viewset URLs
    path('ingest/', DataIngestionViewSet.as_view({'post': 'ingest_file'}), name='file-ingest'),
    path('services/', ServiceViewSet.as_view({'get': 'list_services'}), name='service-list'),
    path('lusha_contact_search/', LushaContactSearchView.as_view(), name='lusha-contact-search'),
    path('lusha_contact_enrich/', LushaContactsEnrichView.as_view(), name='lusha-contact-enrich')
]
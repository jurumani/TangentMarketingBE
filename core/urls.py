# core/urls.py

from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.permissions import AllowAny  # Use AllowAny for public access

schema_view = get_schema_view(
    openapi.Info(
        title="Your API",
        default_version='v1',
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@yourapi.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(AllowAny,),  # Set to AllowAny for public access
)

urlpatterns = [
    path('admin/', admin.site.urls),
    #path('accounts/', include('allauth.urls')),  # Include Allauth URLs
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('users/', include('users.urls')),  # Include users app URLs
    path('utilities/', include('utilities.urls')),  # Include the utilities app's URLs
    path('messaging/', include('messaging.urls')),
    path('datahub/', include('datahub.urls')),
    path('engage/', include('engage.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

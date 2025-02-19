from django.urls import path
from .views import get_csrf_token
from .views import verify_email

urlpatterns = [
    path('get-csrf-token/', get_csrf_token, name='get-csrf-token'),
    path('verify-email/', verify_email, name='verify-email'),
]

# engage/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("waapi/get_qr_code/", views.get_qr_code, name="get_qr_code"),
    path("waapi/check_status/", views.check_waapi_status, name="check_waapi_status"),
    path("waapi/webhook/", views.waapi_webhook, name='waapi_webhook'),
    path('waapi/get_instance_id/', views.get_instance_id, name='get_instance_id'),
    path('waapi/download_convert_base64/', views.download_and_convert_to_base64, name='download_and_convert_to_base64'),
]

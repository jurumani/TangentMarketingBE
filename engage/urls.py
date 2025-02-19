# engage/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("waapi/get_qr_code/", views.get_qr_code, name="get_qr_code"),
    path("waapi/check_status/", views.check_waapi_status, name="check_waapi_status"),
]

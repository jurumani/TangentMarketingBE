# engage/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.register(r'videos', views.SynthesiaVideoViewSet)


urlpatterns = [
    path("waapi/get_qr_code/", views.get_qr_code, name="get_qr_code"),
    path("waapi/check_status/", views.check_waapi_status, name="check_waapi_status"),
    path("waapi/webhook/", views.waapi_webhook, name='waapi_webhook'),
    path('', include(router.urls)),
]


from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MessageViewSet

router = DefaultRouter()
router.register(r'messages', MessageViewSet, basename='message')  # Explicitly specify the basename

urlpatterns = [
    path('', include(router.urls)),
]

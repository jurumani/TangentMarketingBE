from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UsersViewSet, CustomSignupView, CustomLoginView, CustomLogoutView, CustomPasswordResetView, CustomPasswordResetConfirmView, CustomPasswordResetFromKeyView


router = DefaultRouter()
router.register(r'', UsersViewSet, basename='users')

urlpatterns = [
    path('signup/', CustomSignupView.as_view(), name='signup'),  # Your custom signup view
    path('login/', CustomLoginView.as_view(), name='login'),  # Custom login for API
    path('logout/', CustomLogoutView.as_view(), name='logout'),  # Custom logout for API,
    path('password-reset/', CustomPasswordResetView.as_view(), name='password-reset'),  # Custom password reset view
    path('password-reset/key/<uidb64>/<token>/', CustomPasswordResetFromKeyView.as_view(), name='password_reset_from_key'),
    path('password-reset-confirm/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('', include(router.urls)),
]

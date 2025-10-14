from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from . import views
from . import verification_views

app_name = 'authentication'

# Create router for verification viewsets
router = DefaultRouter()
router.register(r'documents', verification_views.DocumentUploadViewSet, basename='document')
router.register(r'verifications', verification_views.VerificationViewSet, basename='verification')
router.register(r'admin-verification', verification_views.AdminVerificationDashboardViewSet, basename='admin-verification')

urlpatterns = [
    # Authentication endpoints
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh_token'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # User profile
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    
    # Verification endpoints (from router)
    path('', include(router.urls)),
]
            
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from . import views
from . import verification_views
from . import nearby_views
from . import moderation_views
from .password_views import (
    PasswordResetRequestView,
    PasswordResetConfirmView,
    PasswordResetVerifyView,
)

app_name = 'authentication'

# Create router for verification viewsets
router = DefaultRouter()
router.register(r'documents', verification_views.DocumentUploadViewSet, basename='document')
router.register(r'verifications', verification_views.VerificationViewSet, basename='verification')
router.register(r'admin-verification', verification_views.AdminVerificationDashboardViewSet, basename='admin-verification')

urlpatterns = [
    # Authentication endpoints
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('admin-login/', views.AdminLoginView.as_view(), name='admin-login'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh_token'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('reset-password/', PasswordResetRequestView.as_view(), name='reset-password'),
    path(
        'verify-reset-otp/',
        PasswordResetVerifyView.as_view(),
        name='verify-reset-otp',
    ),
    path(
        'confirm-reset-password/',
        PasswordResetConfirmView.as_view(),
        name='confirm-reset-password',
    ),
    
    # User profile
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile-picture/', views.UpdateProfilePictureView.as_view(), name='update-profile-picture'),
    path('associated-law-firm/', views.UpdateAssociatedLawFirmView.as_view(), name='update-associated-law-firm'),
    path('change-role/', views.change_user_role, name='change-role'),
    
    # User search
    path('users/search/', views.UserSearchView.as_view(), name='user-search'),
    
    # Consultations
    path('consultations/', views.professional_consultations, name='professional-consultations'),
    
    # Nearby search
    path('nearby-legal-professionals/', nearby_views.nearby_legal_professionals, name='nearby-legal-professionals'),
    
    # Moderation: Block / Report
    path('block/', moderation_views.BlockUserView.as_view(), name='block-user'),
    path('block/<int:user_id>/unblock/', moderation_views.UnblockUserView.as_view(), name='unblock-user'),
    path('blocked-users/', moderation_views.BlockedUsersListView.as_view(), name='blocked-users-list'),
    path('block/<int:user_id>/check/', moderation_views.CheckBlockedView.as_view(), name='check-blocked'),
    path('report/', moderation_views.ReportUserView.as_view(), name='report-user'),
    path('reports/', moderation_views.MyReportsListView.as_view(), name='my-reports'),
    path('reports/<int:pk>/', moderation_views.ReportDetailView.as_view(), name='report-detail'),
    
    # Verification endpoints (from router)
    path('', include(router.urls)),
]
            
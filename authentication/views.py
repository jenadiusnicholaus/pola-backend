from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import (
    UserRegistrationSerializer,
    UserDetailSerializer,
)

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    
    Supports registration for different user roles:
    - Advocate
    - Lawyer
    - Paralegal
    - Law Firm
    - Law Student
    - Citizen
    
    Each role has specific required fields. See the model documentation for details.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Register a new user with role-specific information",
        responses={
            201: openapi.Response(
                description="User created successfully"
            ),
            400: "Bad Request - Validation errors"
        },
        tags=['Authentication']
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Return minimal user info
        return Response(
            {
                'message': 'User registered successfully. Please verify your account.',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'user_role': user.user_role.role_name if user.user_role else None,
                    'is_verified': user.is_verified,
                }
            },
            status=status.HTTP_201_CREATED
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint to retrieve and update user profile.
    """
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_context(self):
        """Ensure request is passed to serializer context"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @swagger_auto_schema(
        operation_description="Get current user profile",
        responses={200: UserDetailSerializer},
        tags=['User Profile']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Update current user profile",
        responses={200: UserDetailSerializer},
        tags=['User Profile']
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Partially update current user profile",
        responses={200: UserDetailSerializer},
        tags=['User Profile']
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class AdminLoginView(APIView):
    """
    API endpoint for admin login.
    
    Authenticates admin users and returns JWT tokens.
    Only users with staff or superuser status can login through this endpoint.
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Admin login - Returns JWT tokens for authenticated admin users",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Admin email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Admin password'),
            },
        ),
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description='JWT access token'),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='JWT refresh token'),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'is_superuser': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            }
                        ),
                    }
                )
            ),
            400: "Bad Request - Invalid credentials",
            403: "Forbidden - User is not an admin",
        },
        tags=['Authentication']
    )
    def post(self, request):
        from django.contrib.auth import authenticate
        from rest_framework_simplejwt.tokens import RefreshToken
        
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Please provide both email and password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is None:
            return Response(
                {'error': 'Invalid email or password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is admin (staff or superuser)
        if not (user.is_staff or user.is_superuser):
            return Response(
                {'error': 'You do not have admin access'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response(
            {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                }
            },
            status=status.HTTP_200_OK
        )


class UpdateProfilePictureView(APIView):
    """
    API endpoint for updating user profile picture.
    
    Allows any authenticated user to update their profile picture.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Update user profile picture",
        manual_parameters=[
            openapi.Parameter(
                'profile_picture',
                openapi.IN_FORM,
                description="Profile picture image file (JPEG/PNG, max 5MB)",
                type=openapi.TYPE_FILE,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Profile picture updated successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Profile picture updated successfully",
                        "profile_picture_url": "https://api.pola.co.tz/media/profile_pictures/user_123.jpg"
                    }
                }
            ),
            400: "Bad Request - Invalid file or file too large",
            401: "Unauthorized - Authentication required"
        },
        tags=['Authentication']
    )
    def patch(self, request):
        user = request.user
        profile_picture = request.FILES.get('profile_picture')
        
        if not profile_picture:
            return Response(
                {'error': 'No profile picture provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
        if profile_picture.content_type not in allowed_types:
            return Response(
                {'error': 'Invalid file type. Only JPEG and PNG images are allowed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (5MB max)
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        if profile_picture.size > max_size:
            return Response(
                {'error': 'File too large. Maximum size is 5MB'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Delete old profile picture if exists
        if user.profile_picture:
            try:
                user.profile_picture.delete(save=False)
            except Exception:
                pass  # Ignore errors when deleting old file
        
        # Update profile picture
        user.profile_picture = profile_picture
        user.save()
        
        # Build full URL for profile picture
        profile_picture_url = request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None
        
        return Response(
            {
                'success': True,
                'message': 'Profile picture updated successfully',
                'profile_picture_url': profile_picture_url
            },
            status=status.HTTP_200_OK
        )

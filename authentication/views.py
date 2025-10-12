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

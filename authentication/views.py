from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import (
    UserRegistrationSerializer,
    UserDetailSerializer,
)
from .models import UserRole, Verification, Document

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
    parser_classes = [MultiPartParser, FormParser]
    
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


@swagger_auto_schema(
    method='post',
    operation_description="Change user role (e.g., from law_student to lawyer after graduation). Requires re-verification.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['new_role'],
        properties={
            'new_role': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='New role name',
                enum=['advocate', 'lawyer', 'paralegal', 'law_firm', 'law_student', 'citizen']
            ),
            'reason': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Reason for role change (e.g., "Graduated from law school")'
            ),
        },
    ),
    responses={
        200: openapi.Response(
            description="Role change initiated successfully",
            examples={
                "application/json": {
                    "message": "Role change initiated. Please submit required documents for verification.",
                    "new_role": "lawyer",
                    "verification_required": True,
                    "is_verified": False
                }
            }
        ),
        400: "Bad Request - Invalid role or same as current role",
        401: "Unauthorized - Authentication required"
    },
    tags=['User Profile']
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_user_role(request):
    """Change user role. Professional roles retain verification, others need re-verification."""
    user = request.user
    new_role_name = request.data.get('new_role')
    reason = request.data.get('reason', '')
    
    if not new_role_name:
        return Response({'error': 'new_role is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        new_role = UserRole.objects.get(role_name=new_role_name)
    except UserRole.DoesNotExist:
        return Response({'error': f'Invalid role: {new_role_name}'}, status=status.HTTP_400_BAD_REQUEST)
    
    if user.user_role and user.user_role.id == new_role.id:
        return Response({'error': 'New role is the same as your current role'}, status=status.HTTP_400_BAD_REQUEST)
    
    with transaction.atomic():
        old_role_name = user.user_role.role_name if user.user_role else None
        professional_roles = ['advocate', 'lawyer', 'paralegal', 'law_firm']
        
        # Prevent professionals from switching to non-professional roles
        if old_role_name in professional_roles and new_role_name not in professional_roles:
            return Response({
                'error': 'Professionals cannot switch to student or citizen roles. Please contact support if you need to change your account type.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # All role changes require re-verification (each role has different document requirements)
        user.user_role = new_role
        user.save()
        
        # Update verification record to pending (requires new documents for new role)
        verification, _ = Verification.objects.get_or_create(user=user)
        verification.status = 'pending'
        note = f'Role change: {old_role_name} → {new_role_name}. {reason}. Must submit documents for new role.'
        verification.verification_notes = f'{verification.verification_notes}\n{note}' if verification.verification_notes else note
        verification.save()
    
    return Response({
        'message': 'Role changed. Please submit required documents for your new role.',
        'old_role': old_role_name,
        'new_role': new_role_name,
        'is_verified': user.is_verified,  # Read-only property from verification model
        'verification_required': True
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    operation_description="Get all consultations for the authenticated professional (advocate, lawyer, paralegal, law_firm)",
    manual_parameters=[
        openapi.Parameter(
            'status',
            openapi.IN_QUERY,
            description="Filter by consultation status (pending, completed, cancelled)",
            type=openapi.TYPE_STRING,
            enum=['pending', 'completed', 'cancelled']
        ),
        openapi.Parameter(
            'type',
            openapi.IN_QUERY,
            description="Filter by consultation type (mobile, physical)",
            type=openapi.TYPE_STRING,
            enum=['mobile', 'physical']
        ),
        openapi.Parameter(
            'limit',
            openapi.IN_QUERY,
            description="Number of results per page (default: 20, max: 100)",
            type=openapi.TYPE_INTEGER
        ),
    ],
    responses={
        200: openapi.Response(
            description="List of consultations",
            examples={
                "application/json": {
                    "count": 10,
                    "consultations": [
                        {
                            "id": 1,
                            "client": {
                                "id": 42,
                                "name": "John Doe",
                                "email": "john@example.com",
                                "phone": "+255712345678"
                            },
                            "type": "mobile",
                            "status": "pending",
                            "scheduled_time": "2025-12-15T14:00:00Z",
                            "duration_minutes": 30,
                            "amount_paid": "50000.00",
                            "professional_earnings": "25000.00",
                            "created_at": "2025-12-13T10:00:00Z"
                        }
                    ],
                    "statistics": {
                        "total_consultations": 10,
                        "total_earnings": "250000.00",
                        "pending_count": 3,
                        "completed_count": 6,
                        "cancelled_count": 1
                    }
                }
            }
        ),
        401: "Unauthorized - Authentication required"
    },
    tags=['Consultations']
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def professional_consultations(request):
    """
    Get all consultations for the authenticated user.
    Returns consultations based on user role:
    - Professionals: consultations where they are the provider
    - Citizens/Students: consultations where they are the client
    - Any type: mobile, physical, video, legal_aid, document_review, etc.
    """
    user = request.user
    
    # TODO: Replace with actual consultation model when implemented
    # This endpoint will work for ALL user types, filtering appropriately
    consultations = []
    
    # Get query parameters
    status_filter = request.query_params.get('status')
    type_filter = request.query_params.get('type')  # Can be any consultation type
    role_filter = request.query_params.get('role', 'provider')  # 'provider' or 'client'
    try:
        limit = int(request.query_params.get('limit', 20))
        limit = max(1, min(100, limit))
    except ValueError:
        limit = 20
    
    # Determine user's perspective
    is_professional = user.user_role and user.user_role.role_name in ['advocate', 'lawyer', 'paralegal', 'law_firm']
    
    # Statistics (will vary based on role)
    statistics = {
        'total_consultations': 0,
        'total_amount': '0.00',  # For clients: total spent, For professionals: total earned
        'pending_count': 0,
        'completed_count': 0,
        'cancelled_count': 0
    }
    
    return Response(
        {
            'count': len(consultations),
            'consultations': consultations,
            'statistics': statistics,
            'user_role': user.user_role.role_name if user.user_role else None,
            'viewing_as': 'provider' if is_professional else 'client',
            'message': 'Consultation system integration pending. This endpoint supports all consultation types and user roles.'
        },
        status=status.HTTP_200_OK
    )

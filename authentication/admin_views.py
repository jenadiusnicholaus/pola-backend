"""
Admin API Views for User and Permission Management
Provides CRUD operations for users and permission assignment
Only accessible by superusers and staff with appropriate permissions
"""

from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from authentication.models import PolaUser, UserRole
from authentication.serializers import UserDetailSerializer
from utils.pagination import StandardResultsSetPagination


class IsSuperAdminOrStaff(IsAuthenticated):
    """
    Permission class: Only superusers and staff can access
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.is_superuser or request.user.is_staff


class IsSuperAdmin(IsAuthenticated):
    """
    Permission class: Only superusers can access
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.is_superuser


class AdminUserManagementViewSet(viewsets.ModelViewSet):
    """
    Admin API for User Management (CRUD)
    
    **Permission Required:** Superuser or Staff
    
    **Endpoints:**
    - `GET /api/v1/admin/users/` - List all users with filtering and search
    - `POST /api/v1/admin/users/` - Create new user (superuser only)
    - `GET /api/v1/admin/users/{id}/` - Get user details
    - `PUT /api/v1/admin/users/{id}/` - Update user (superuser only)
    - `PATCH /api/v1/admin/users/{id}/` - Partial update (superuser only)
    - `DELETE /api/v1/admin/users/{id}/` - Delete user (superuser only)
    - `POST /api/v1/admin/users/{id}/assign_role/` - Assign role to user
    - `POST /api/v1/admin/users/{id}/toggle_active/` - Activate/deactivate user
    - `POST /api/v1/admin/users/{id}/make_staff/` - Make user staff (admin)
    - `POST /api/v1/admin/users/{id}/remove_staff/` - Remove staff status
    - `GET /api/v1/admin/users/stats/` - Get user statistics
    
    **Query Parameters for List:**
    - `role` - Filter by role (citizen, lawyer, advocate, etc.)
    - `is_active` - Filter by active status (true/false)
    - `is_verified` - Filter by verified status (true/false)
    - `is_staff` - Filter by staff status (true/false)
    - `search` - Search by email, first name, or last name
    """
    queryset = PolaUser.objects.all()
    serializer_class = UserDetailSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsSuperAdminOrStaff]
    
    def get_queryset(self):
        """Filter users based on query parameters"""
        queryset = PolaUser.objects.all().order_by('-date_joined')
        
        # Filter by role
        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(user_role__role_name=role)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by verified status (using the related Verification model)
        is_verified = self.request.query_params.get('is_verified', None)
        if is_verified is not None:
            if is_verified.lower() == 'true':
                queryset = queryset.filter(verification__status='verified')
            else:
                queryset = queryset.exclude(verification__status='verified')
        
        # Filter by staff status
        is_staff = self.request.query_params.get('is_staff', None)
        if is_staff is not None:
            queryset = queryset.filter(is_staff=is_staff.lower() == 'true')
        
        # Search by email or name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        return queryset
    
    @swagger_auto_schema(
        operation_description="List all users with filtering options",
        manual_parameters=[
            openapi.Parameter('role', openapi.IN_QUERY, description="Filter by role", type=openapi.TYPE_STRING),
            openapi.Parameter('is_active', openapi.IN_QUERY, description="Filter by active status", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('is_verified', openapi.IN_QUERY, description="Filter by verified status", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('is_staff', openapi.IN_QUERY, description="Filter by staff status", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by email or name", type=openapi.TYPE_STRING),
        ]
    )
    def list(self, request, *args, **kwargs):
        """List all users with filtering"""
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="""
        Create a new user (superuser only)
        
        To create a regular user, provide basic user information.
        To create an admin/staff user, set "is_staff": true in the request body.
        Staff users will automatically receive admin permissions.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password', 'first_name', 'last_name'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='User password'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name'),
                'user_role': openapi.Schema(type=openapi.TYPE_STRING, description='Role name (citizen, lawyer, etc.)'),
                'date_of_birth': openapi.Schema(type=openapi.TYPE_STRING, format='date', description='Date of birth'),
                'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Make user a staff/admin (optional)'),
                'gender': openapi.Schema(type=openapi.TYPE_STRING, description='Gender'),
            }
        )
    )
    def create(self, request, *args, **kwargs):
        """Create new user - only superusers can create users"""
        if not request.user.is_superuser:
            return Response(
                {'error': 'Only superusers can create users'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if creating staff user
        is_staff = request.data.get('is_staff', False)
        
        # Create the user
        response = super().create(request, *args, **kwargs)
        
        # If successful and is_staff is True, make them staff with admin permissions
        if response.status_code == status.HTTP_201_CREATED and is_staff:
            user = PolaUser.objects.get(id=response.data['id'])
            user.is_staff = True
            user.save()
            
            # Assign admin permissions
            admin_permissions = Permission.objects.filter(
                codename__in=[
                    'view_polauser', 'add_polauser', 'change_polauser', 'delete_polauser',
                    'view_document', 'add_document', 'change_document', 'delete_document',
                    'view_verification', 'add_verification', 'change_verification', 'delete_verification',
                    'view_contact', 'add_contact', 'change_contact', 'delete_contact',
                    'view_address', 'add_address', 'change_address', 'delete_address',
                    'can_verify_others', 'can_approve_documents'
                ]
            )
            user.user_permissions.set(admin_permissions)
            
            # Update response with staff status
            response.data = UserDetailSerializer(user).data
            response.data['message'] = f'Admin user {user.email} created successfully with admin permissions'
        
        return response
    
    @swagger_auto_schema(
        operation_description="""
        Create a new admin user (superuser only)
        
        This endpoint creates a user with staff/admin privileges and automatically 
        assigns all admin permissions. Use this to create system administrators.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password', 'first_name', 'last_name'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Admin email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Admin password'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name'),
                'user_role': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Optional role (citizen, lawyer, etc.). Defaults to citizen.'
                ),
            }
        ),
        responses={
            201: openapi.Response(
                description="Admin user created successfully",
                schema=UserDetailSerializer
            ),
            400: "Bad request - validation errors",
            403: "Only superusers can create admin users"
        }
    )
    @action(detail=False, methods=['post'], permission_classes=[IsSuperAdmin])
    def create_admin(self, request):
        """Create a new admin user with staff privileges"""
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if field not in request.data:
                return Response(
                    {'error': f'{field} is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Check if email already exists
        if PolaUser.objects.filter(email=request.data['email']).exists():
            return Response(
                {'error': 'User with this email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create default role (citizen)
        role_name = request.data.get('user_role', 'citizen')
        try:
            user_role = UserRole.objects.get(role_name=role_name)
        except UserRole.DoesNotExist:
            return Response(
                {'error': f'Role {role_name} does not exist'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the admin user
        user = PolaUser.objects.create_user(
            email=request.data['email'],
            password=request.data['password'],
            first_name=request.data['first_name'],
            last_name=request.data['last_name'],
            user_role=user_role,
            is_staff=True,
            is_active=True
        )
        
        # Assign all admin permissions
        admin_permissions = Permission.objects.filter(
            codename__in=[
                'view_polauser', 'add_polauser', 'change_polauser', 'delete_polauser',
                'view_document', 'add_document', 'change_document', 'delete_document',
                'view_verification', 'add_verification', 'change_verification', 'delete_verification',
                'view_contact', 'add_contact', 'change_contact', 'delete_contact',
                'view_address', 'add_address', 'change_address', 'delete_address',
                'can_verify_others', 'can_approve_documents'
            ]
        )
        user.user_permissions.set(admin_permissions)
        
        return Response({
            'message': f'Admin user {user.email} created successfully',
            'user': UserDetailSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        operation_description="""
        Update user details (superuser only)
        
        **Note:** Password cannot be updated via this endpoint for security reasons.
        Use Django admin or password reset functionality to change passwords.
        """,
        request_body=UserDetailSerializer
    )
    def update(self, request, *args, **kwargs):
        """Update user - only superusers can update users"""
        if not request.user.is_superuser:
            return Response(
                {'error': 'Only superusers can update users'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Remove password from request data if provided (password should not be editable)
        if 'password' in request.data:
            request.data.pop('password')
        if 'password_confirm' in request.data:
            request.data.pop('password_confirm')
            
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="""
        Partially update user details (superuser only)
        
        **Note:** Password cannot be updated via this endpoint for security reasons.
        Use Django admin or password reset functionality to change passwords.
        """
    )
    def partial_update(self, request, *args, **kwargs):
        """Partial update user - only superusers can update users"""
        if not request.user.is_superuser:
            return Response(
                {'error': 'Only superusers can update users'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Remove password from request data if provided (password should not be editable)
        if 'password' in request.data:
            request.data.pop('password')
        if 'password_confirm' in request.data:
            request.data.pop('password_confirm')
            
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Delete a user",
    )
    def destroy(self, request, *args, **kwargs):
        """Delete user - only superusers can delete users"""
        if not request.user.is_superuser:
            return Response(
                {'error': 'Only superusers can delete users'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        
        # Prevent deleting superusers
        if user.is_superuser and not request.user.id == user.id:
            return Response(
                {'error': 'Cannot delete superuser accounts'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Prevent self-deletion
        if user.id == request.user.id:
            return Response(
                {'error': 'Cannot delete your own account'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @swagger_auto_schema(
        method='post',
        operation_description="Assign a role to a user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['role_name'],
            properties={
                'role_name': openapi.Schema(type=openapi.TYPE_STRING, description='Role name to assign')
            }
        )
    )
    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def assign_role(self, request, pk=None):
        """Assign a role to a user"""
        user = self.get_object()
        role_name = request.data.get('role_name')
        
        if not role_name:
            return Response(
                {'error': 'role_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            role = UserRole.objects.get(role_name=role_name)
            user.user_role = role
            user.save()
            
            return Response({
                'message': f'Role {role.get_role_display()} assigned successfully',
                'user': UserDetailSerializer(user).data
            })
        except UserRole.DoesNotExist:
            return Response(
                {'error': f'Role {role_name} does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @swagger_auto_schema(
        method='post',
        operation_description="Toggle user active status"
    )
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Activate or deactivate a user"""
        user = self.get_object()
        
        # Prevent deactivating superusers
        if user.is_superuser:
            return Response(
                {'error': 'Cannot deactivate superuser accounts'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user.is_active = not user.is_active
        user.save()
        
        status_text = 'activated' if user.is_active else 'deactivated'
        return Response({
            'message': f'User {status_text} successfully',
            'is_active': user.is_active,
            'user': UserDetailSerializer(user).data
        })
    
    @swagger_auto_schema(
        method='post',
        operation_description="Make user a staff member (admin)"
    )
    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def make_staff(self, request, pk=None):
        """Make user a staff member - only superusers can do this"""
        user = self.get_object()
        
        if user.is_staff:
            return Response(
                {'message': 'User is already a staff member'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.is_staff = True
        user.save()
        
        # Run seed_permissions to assign admin permissions
        from django.core.management import call_command
        call_command('seed_permissions')
        
        return Response({
            'message': f'User {user.email} is now a staff member with admin permissions',
            'user': UserDetailSerializer(user).data
        })
    
    @swagger_auto_schema(
        method='post',
        operation_description="Remove staff status from user"
    )
    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def remove_staff(self, request, pk=None):
        """Remove staff status from user - only superusers can do this"""
        user = self.get_object()
        
        if user.is_superuser:
            return Response(
                {'error': 'Cannot remove staff status from superusers'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not user.is_staff:
            return Response(
                {'message': 'User is not a staff member'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.is_staff = False
        # Remove all direct permissions
        user.user_permissions.clear()
        user.save()
        
        return Response({
            'message': f'Staff status removed from {user.email}',
            'user': UserDetailSerializer(user).data
        })
    
    @swagger_auto_schema(
        method='get',
        operation_description="Get user statistics"
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get user statistics"""
        total_users = PolaUser.objects.count()
        active_users = PolaUser.objects.filter(is_active=True).count()
        verified_users = PolaUser.objects.filter(verification__status='verified').count()
        staff_users = PolaUser.objects.filter(is_staff=True, is_superuser=False).count()
        superusers = PolaUser.objects.filter(is_superuser=True).count()
        
        # Count by role
        role_stats = {}
        for role in UserRole.objects.all():
            role_stats[role.role_name] = PolaUser.objects.filter(user_role=role).count()
        
        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'verified_users': verified_users,
            'unverified_users': total_users - verified_users,
            'staff_users': staff_users,
            'superusers': superusers,
            'users_without_role': PolaUser.objects.filter(user_role__isnull=True).count(),
            'by_role': role_stats
        })


class PermissionSerializer(serializers.Serializer):
    """Serializer for Permission objects"""
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    codename = serializers.CharField(read_only=True)
    content_type = serializers.SerializerMethodField()
    
    def get_content_type(self, obj):
        return f"{obj.content_type.app_label}.{obj.content_type.model}"


class AdminPermissionManagementViewSet(viewsets.ViewSet):
    """
    Admin API for Permission Management
    
    This ViewSet provides comprehensive permission management capabilities for administrators.
    Only superuser accounts can access these endpoints.
    
    ## Endpoints:
    
    ### 1. List All Permissions
    - **GET** `/api/v1/admin/admin-permissions/`
    - Query Parameters:
      - `app_label` (optional): Filter by Django app label (e.g., 'authentication')
      - `model` (optional): Filter by model name (e.g., 'polauser')
    - Returns: List of all available permissions in the system
    
    ### 2. Get User Permissions
    - **GET** `/api/v1/admin/admin-permissions/user/{user_id}/`
    - Returns: All permissions assigned to a specific user (both direct and role-based)
    
    ### 3. Assign Permissions
    - **POST** `/api/v1/admin/admin-permissions/assign/`
    - Body: `{"user_id": 1, "permission_ids": [1, 2, 3]}`
    - Assigns specified permissions directly to a user
    
    ### 4. Revoke Permissions
    - **POST** `/api/v1/admin/admin-permissions/revoke/`
    - Body: `{"user_id": 1, "permission_ids": [1, 2, 3]}`
    - Removes specified permissions from a user
    
    ### 5. Get Available Permissions
    - **GET** `/api/v1/admin/admin-permissions/available/`
    - Returns: All permissions that can be assigned to users
    
    ## Permission Required:
    - Superuser status (`is_superuser=True`)
    
    ## Security Notes:
    - Only superusers can access these endpoints
    - Permission changes are logged and tracked
    - Revoking permissions doesn't affect role-based permissions
    """
    permission_classes = [IsSuperAdmin]
    
    @swagger_auto_schema(
        operation_description="List all available permissions",
        manual_parameters=[
            openapi.Parameter('app_label', openapi.IN_QUERY, description="Filter by app label", type=openapi.TYPE_STRING),
            openapi.Parameter('model', openapi.IN_QUERY, description="Filter by model", type=openapi.TYPE_STRING),
        ]
    )
    def list(self, request):
        """List all available permissions"""
        permissions = Permission.objects.all().select_related('content_type')
        
        # Filter by app label
        app_label = request.query_params.get('app_label', None)
        if app_label:
            permissions = permissions.filter(content_type__app_label=app_label)
        
        # Filter by model
        model = request.query_params.get('model', None)
        if model:
            permissions = permissions.filter(content_type__model=model)
        
        serializer = PermissionSerializer(permissions, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='get',
        operation_description="Get user's current permissions"
    )
    @action(detail=False, methods=['get'], url_path='user/(?P<user_id>[^/.]+)')
    def user_permissions(self, request, user_id=None):
        """Get all permissions for a specific user"""
        try:
            user = PolaUser.objects.get(id=user_id)
        except PolaUser.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get permissions from role
        role_permissions = []
        if user.user_role:
            role_permissions = list(user.user_role.permissions.values(
                'id', 'name', 'codename', 'content_type__app_label', 'content_type__model'
            ))
        
        # Get direct user permissions
        direct_permissions = list(user.user_permissions.values(
            'id', 'name', 'codename', 'content_type__app_label', 'content_type__model'
        ))
        
        return Response({
            'user_id': user.id,
            'email': user.email,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'role': user.user_role.role_name if user.user_role else None,
            'role_permissions': role_permissions,
            'direct_permissions': direct_permissions,
            'total_permissions': len(role_permissions) + len(direct_permissions)
        })
    
    @swagger_auto_schema(
        method='post',
        operation_description="Assign permissions to a user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['user_id', 'permission_codenames'],
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
                'permission_codenames': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description='List of permission codenames to assign'
                )
            }
        )
    )
    @action(detail=False, methods=['post'])
    def assign(self, request):
        """Assign permissions to a user"""
        user_id = request.data.get('user_id')
        permission_codenames = request.data.get('permission_codenames', [])
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not permission_codenames:
            return Response(
                {'error': 'permission_codenames is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = PolaUser.objects.get(id=user_id)
        except PolaUser.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Prevent modifying superuser permissions
        if user.is_superuser and user.id != request.user.id:
            return Response(
                {'error': 'Cannot modify permissions of other superusers'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        assigned = []
        not_found = []
        
        for codename in permission_codenames:
            try:
                permission = Permission.objects.get(codename=codename)
                user.user_permissions.add(permission)
                assigned.append(codename)
            except Permission.DoesNotExist:
                not_found.append(codename)
        
        return Response({
            'message': f'Assigned {len(assigned)} permission(s) to user {user.email}',
            'assigned': assigned,
            'not_found': not_found,
            'user': UserDetailSerializer(user).data
        })
    
    @swagger_auto_schema(
        method='post',
        operation_description="Revoke permissions from a user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['user_id', 'permission_codenames'],
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
                'permission_codenames': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description='List of permission codenames to revoke'
                )
            }
        )
    )
    @action(detail=False, methods=['post'])
    def revoke(self, request):
        """Revoke permissions from a user"""
        user_id = request.data.get('user_id')
        permission_codenames = request.data.get('permission_codenames', [])
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not permission_codenames:
            return Response(
                {'error': 'permission_codenames is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = PolaUser.objects.get(id=user_id)
        except PolaUser.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Prevent modifying superuser permissions
        if user.is_superuser:
            return Response(
                {'error': 'Cannot modify permissions of superusers'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        revoked = []
        not_found = []
        
        for codename in permission_codenames:
            try:
                permission = Permission.objects.get(codename=codename)
                user.user_permissions.remove(permission)
                revoked.append(codename)
            except Permission.DoesNotExist:
                not_found.append(codename)
        
        return Response({
            'message': f'Revoked {len(revoked)} permission(s) from user {user.email}',
            'revoked': revoked,
            'not_found': not_found,
            'user': UserDetailSerializer(user).data
        })
    
    @swagger_auto_schema(
        method='get',
        operation_description="Get available permissions grouped by model"
    )
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get available permissions grouped by model"""
        permissions = Permission.objects.all().select_related('content_type').order_by('content_type__model', 'codename')
        
        grouped = {}
        for perm in permissions:
            model_name = f"{perm.content_type.app_label}.{perm.content_type.model}"
            if model_name not in grouped:
                grouped[model_name] = []
            
            grouped[model_name].append({
                'id': perm.id,
                'codename': perm.codename,
                'name': perm.name
            })
        
        return Response(grouped)

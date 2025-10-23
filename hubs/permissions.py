"""
Unified Hub Permissions - Works for all hubs (Advocates, Students, Forum)
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthenticatedOrReadOnly(BasePermission):
    """
    Allow unauthenticated read-only access, require authentication for write
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class CanAccessHub(BasePermission):
    """
    Check if user can access specific hub based on hub_type
    - Advocates Hub: Only verified advocates and admins
    - Students Hub: Students, lecturers, and admins  
    - Forum: Everyone (public)
    - Legal Education: Everyone (public)
    """
    message = "You don't have permission to access this hub"
    
    def has_permission(self, request, view):
        # Get hub_type from query params or view kwargs
        hub_type = request.query_params.get('hub_type') or view.kwargs.get('hub_type')
        
        if not hub_type:
            # If no hub_type specified, allow (will be filtered in queryset)
            return True
        
        # Forum and Legal Education are public
        if hub_type in ['forum', 'legal_ed']:
            return True
        
        # Other hubs require authentication
        if not request.user or not request.user.is_authenticated:
            self.message = f"Authentication required to access {hub_type} hub"
            return False
        
        # Advocates Hub - only advocates and admins
        if hub_type == 'advocates':
            if request.user.user_role not in ['advocate', 'admin']:
                self.message = "Only advocates can access the Advocates Hub"
                return False
            
            # Check verification for advocates
            if request.user.user_role == 'advocate':
                if not hasattr(request.user, 'verification') or request.user.verification.status != 'verified':
                    self.message = "You must be a verified advocate to access this hub"
                    return False
        
        # Students Hub - students, lecturers, admins
        elif hub_type == 'students':
            if request.user.user_role not in ['student', 'lecturer', 'admin']:
                self.message = "Only students, lecturers, and admins can access the Students Hub"
                return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """Check object-level permissions"""
        # Get hub_type from object
        hub_type = getattr(obj, 'hub_type', None)
        
        if not hub_type:
            return True
        
        # Same logic as has_permission but using object's hub_type
        if hub_type in ['forum', 'legal_ed']:
            return True
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        if hub_type == 'advocates':
            return request.user.user_role in ['advocate', 'admin']
        
        if hub_type == 'students':
            return request.user.user_role in ['student', 'lecturer', 'admin']
        
        return True


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission to only allow owners to edit/delete
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in SAFE_METHODS:
            return True
        
        # Write permissions only for owner or admin
        if request.user.user_role == 'admin':
            return True
        
        # Check if object has uploader or author field
        owner = getattr(obj, 'uploader', None) or getattr(obj, 'author', None) or getattr(obj, 'sender', None)
        
        return owner == request.user


class CanCreateContent(BasePermission):
    """
    Check if user can create content in specific hub
    """
    message = "You don't have permission to create content in this hub"
    
    def has_permission(self, request, view):
        if request.method not in ['POST', 'PUT', 'PATCH']:
            return True
        
        if not request.user or not request.user.is_authenticated:
            self.message = "Authentication required to create content"
            return False
        
        # Get hub_type from request data
        hub_type = request.data.get('hub_type')
        
        if not hub_type:
            self.message = "hub_type is required"
            return False
        
        # Forum and Legal Ed - different rules
        if hub_type == 'forum':
            return True  # Anyone can post in forum
        
        if hub_type == 'legal_ed':
            # Only admins can create legal education content
            if request.user.user_role != 'admin':
                self.message = "Only admins can create legal education content"
                return False
        
        # Advocates Hub - only advocates and admins
        if hub_type == 'advocates':
            if request.user.user_role not in ['advocate', 'admin']:
                self.message = "Only advocates and admins can post in Advocates Hub"
                return False
            
            # Check verification
            if request.user.user_role == 'advocate':
                if not hasattr(request.user, 'verification') or request.user.verification.status != 'verified':
                    self.message = "You must be a verified advocate"
                    return False
        
        # Students Hub - students, lecturers, admins
        if hub_type == 'students':
            if request.user.user_role not in ['student', 'lecturer', 'admin']:
                self.message = "Only students, lecturers, and admins can post in Students Hub"
                return False
        
        return True


class CanPurchaseContent(BasePermission):
    """
    Check if user can purchase content
    """
    message = "You cannot purchase this content"
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            self.message = "Authentication required to purchase"
            return False
        
        # Cannot purchase your own content
        if obj.uploader == request.user:
            self.message = "You cannot purchase your own content"
            return False
        
        # Content must be paid
        if obj.price == 0:
            self.message = "This content is free"
            return False
        
        # Content must be in students hub (only students hub has paid content)
        if obj.hub_type != 'students':
            self.message = "Only Students Hub content can be purchased"
            return False
        
        return True


class CanFollowLecturer(BasePermission):
    """
    Check if user can follow a lecturer
    """
    message = "Only students can follow lecturers"
    
    def has_permission(self, request, view):
        if request.method not in ['POST', 'DELETE']:
            return True
        
        if not request.user or not request.user.is_authenticated:
            self.message = "Authentication required"
            return False
        
        # Only students can follow lecturers
        if request.user.user_role != 'student':
            self.message = "Only students can follow lecturers"
            return False
        
        return True

"""
Custom Permission Classes for Pola
Defines granular permissions for different user actions
"""

from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to only allow owners of an object or admins to access it.
    """
    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user and request.user.is_staff:
            return True
        
        # Check if object has a user attribute (for most models)
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # For user objects themselves
        return obj == request.user


class CanVerifyUsers(permissions.BasePermission):
    """
    Permission for users who can verify other users (admins)
    """
    def has_permission(self, request, view):
        return request.user and request.user.has_permission('verify_users')


class CanManageDocuments(permissions.BasePermission):
    """
    Permission for users who can manage documents (admins)
    """
    def has_permission(self, request, view):
        return request.user and request.user.has_permission('manage_documents')


class CanUploadDocuments(permissions.BasePermission):
    """
    Permission for users who can upload documents
    """
    def has_permission(self, request, view):
        return request.user and request.user.has_permission('upload_documents')


class CanViewAllProfiles(permissions.BasePermission):
    """
    Permission for users who can view all profiles (admins)
    """
    def has_permission(self, request, view):
        return request.user and request.user.has_permission('view_all_profiles')


class CanManageRoles(permissions.BasePermission):
    """
    Permission for users who can manage roles (super admins)
    """
    def has_permission(self, request, view):
        return request.user and request.user.has_permission('manage_roles')


class IsVerified(permissions.BasePermission):
    """
    Permission that requires user to be verified
    """
    message = "Your account must be verified to perform this action."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_verified


class HasRolePermission(permissions.BasePermission):
    """
    Base permission class that checks role-based permissions
    """
    required_role = None
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if self.required_role:
            return request.user.has_role(self.required_role)
        
        return True


# Role-specific permissions
class IsAdvocate(HasRolePermission):
    """Permission for advocates only"""
    required_role = 'advocate'


class IsLawyer(HasRolePermission):
    """Permission for lawyers only"""
    required_role = 'lawyer'


class IsLawFirm(HasRolePermission):
    """Permission for law firms only"""
    required_role = 'law_firm'


class IsLegalProfessional(permissions.BasePermission):
    """Permission for any legal professional (advocate, lawyer, paralegal, law firm)"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        legal_roles = ['advocate', 'lawyer', 'paralegal', 'law_firm']
        return any(request.user.has_role(role) for role in legal_roles)

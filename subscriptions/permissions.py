"""
Subscription-based permission utilities

These utilities help check user permissions based on their active subscription.
Use these in views to enforce subscription-based access control.
"""

from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from .models import UserSubscription


def get_user_subscription_permissions(user):
    """
    Get subscription permissions for a user
    
    Args:
        user: PolaUser instance
        
    Returns:
        dict: Permissions dictionary with all subscription-based permissions
    """
    try:
        subscription = user.subscription
        return subscription.get_permissions()
    except UserSubscription.DoesNotExist:
        return {
            'is_active': False,
            'can_access_legal_library': False,
            'can_ask_questions': False,
            'can_generate_documents': False,
            'can_receive_legal_updates': False,
            'can_access_forum': False,
            'can_access_student_hub': False,
            'can_purchase_consultations': False,
            'can_purchase_documents': False,
            'can_purchase_learning_materials': False,
        }


def check_subscription_permission(user, permission_name):
    """
    Check if user has a specific subscription permission
    
    Args:
        user: PolaUser instance
        permission_name: Name of the permission to check (e.g., 'can_ask_questions')
        
    Returns:
        bool: True if user has the permission, False otherwise
    """
    # Django admin users (staff/superuser) have all permissions
    if user.is_staff or user.is_superuser:
        return True
    
    permissions = get_user_subscription_permissions(user)
    return permissions.get(permission_name, False)


def require_active_subscription(user):
    """
    Check if user has an active subscription
    
    Args:
        user: PolaUser instance
        
    Raises:
        PermissionDenied: If user doesn't have an active subscription
        
    Returns:
        UserSubscription: The active subscription or None for admin users
    """
    # Django admin users (staff/superuser) bypass subscription requirements
    if user.is_staff or user.is_superuser:
        return None  # Admin users don't need a subscription
    
    try:
        subscription = user.subscription
        if not subscription.is_active():
            raise PermissionDenied({
                'error': 'Subscription expired',
                'message': 'Your subscription has expired. Please renew to continue.',
                'message_sw': 'Usajili wako umeisha. Tafadhali rejea ili kuendelea.',
                'subscription_status': subscription.status,
                'end_date': subscription.end_date.isoformat()
            })
        return subscription
    except UserSubscription.DoesNotExist:
        raise PermissionDenied({
            'error': 'No subscription',
            'message': 'You need an active subscription to access this feature.',
            'message_sw': 'Unahitaji usajili hai ili kufikia kipengele hiki.'
        })


def require_subscription_permission(user, permission_name, custom_message=None):
    """
    Require user to have a specific subscription permission
    
    Args:
        user: PolaUser instance
        permission_name: Name of the permission to check
        custom_message: Optional custom error message
        
    Raises:
        PermissionDenied: If user doesn't have the required permission
    """
    # Django admin users (staff/superuser) have all permissions
    if user.is_staff or user.is_superuser:
        return  # Admin users have all permissions
    
    subscription = require_active_subscription(user)
    permissions = subscription.get_permissions()
    
    if not permissions.get(permission_name, False):
        message = custom_message or f'Your subscription does not include this feature: {permission_name}'
        raise PermissionDenied({
            'error': 'Permission denied',
            'message': message,
            'required_permission': permission_name,
            'current_plan': subscription.plan.name,
            'upgrade_required': True
        })


def check_questions_limit(user):
    """
    Check if user can ask more questions this month
    
    Args:
        user: PolaUser instance
        
    Returns:
        tuple: (can_ask: bool, remaining: int)
    """
    # Django admin users (staff/superuser) have unlimited questions
    if user.is_staff or user.is_superuser:
        return (True, float('inf'))
    
    subscription = require_active_subscription(user)
    can_ask = subscription.can_ask_question()
    
    if subscription.plan.monthly_questions_limit == 0:
        return (True, float('inf'))
    
    remaining = subscription.plan.monthly_questions_limit - subscription.questions_asked_this_month
    return (can_ask, max(0, remaining))


def check_documents_limit(user):
    """
    Check if user can generate free documents this month
    
    Args:
        user: PolaUser instance
        
    Returns:
        tuple: (can_generate: bool, remaining: int)
    """
    # Django admin users (staff/superuser) have unlimited document generation
    if user.is_staff or user.is_superuser:
        return (True, float('inf'))
    
    subscription = require_active_subscription(user)
    can_generate = subscription.can_generate_free_document()
    
    remaining = subscription.plan.free_documents_per_month - subscription.documents_generated_this_month
    return (can_generate, max(0, remaining))


# DRF Permission Classes

class HasActiveSubscription(BasePermission):
    """
    Permission class to check if user has an active subscription
    """
    message = {
        'error': 'Active subscription required',
        'message': 'You need an active subscription to access this resource.',
        'message_sw': 'Unahitaji usajili hai ili kufikia rasilimali hii.'
    }
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Django admin users (staff/superuser) bypass subscription requirements
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        try:
            subscription = request.user.subscription
            return subscription.is_active()
        except UserSubscription.DoesNotExist:
            return False


class CanAccessLegalLibrary(BasePermission):
    """
    Permission class to check if user can access legal library
    """
    message = {
        'error': 'Legal library access denied',
        'message': 'Your subscription does not include access to the legal library.',
        'upgrade_required': True
    }
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Django admin users (staff/superuser) have access to all features
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        return check_subscription_permission(request.user, 'can_access_legal_library')


class CanAskQuestions(BasePermission):
    """
    Permission class to check if user can ask questions
    """
    message = {
        'error': 'Question limit reached',
        'message': 'You have reached your monthly question limit.',
        'upgrade_required': True
    }
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Django admin users (staff/superuser) can ask unlimited questions
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        try:
            subscription = request.user.subscription
            if not subscription.is_active():
                return False
            
            return subscription.can_ask_question()
        except UserSubscription.DoesNotExist:
            return False


class CanAccessForum(BasePermission):
    """
    Permission class to check if user can access forums
    """
    message = {
        'error': 'Forum access denied',
        'message': 'Your subscription does not include forum access.',
        'upgrade_required': True
    }
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Django admin users (staff/superuser) have forum access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        return check_subscription_permission(request.user, 'can_access_forum')


class CanAccessStudentHub(BasePermission):
    """
    Permission class to check if user can access student hub
    """
    message = {
        'error': 'Student hub access denied',
        'message': 'Your subscription does not include student hub access.',
        'upgrade_required': True
    }
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Django admin users (staff/superuser) have student hub access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        return check_subscription_permission(request.user, 'can_access_student_hub')


# Helper decorators for views

def subscription_required(permission_name=None):
    """
    Decorator to require active subscription for a view function
    
    Usage:
        @subscription_required()
        def my_view(request):
            # Your code here
            
        @subscription_required('can_ask_questions')
        def ask_question(request):
            # Your code here
    """
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            user = request.user
            
            # Check if user is authenticated
            if not user or not user.is_authenticated:
                raise PermissionDenied({
                    'error': 'Authentication required',
                    'message': 'You must be logged in to access this resource.'
                })
            
            # Check for active subscription
            require_active_subscription(user)
            
            # Check specific permission if provided
            if permission_name:
                require_subscription_permission(user, permission_name)
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

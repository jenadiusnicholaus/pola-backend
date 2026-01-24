"""
Subscription-based and Role-based permission utilities

These utilities help check user permissions based on their active subscription
and user role (professional vs citizen/student/lecturer).
Use these in views to enforce access control.
"""

from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from .models import UserSubscription


def is_professional(user):
    """
    Check if user is a professional (advocate, lawyer, paralegal, law_firm)
    
    Args:
        user: PolaUser instance
        
    Returns:
        bool: True if user is a professional
    """
    if not hasattr(user, 'user_role') or not user.user_role:
        return False
    return user.user_role.role_name in ['advocate', 'lawyer', 'paralegal', 'law_firm']


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
        # Check if user is an advocate or lawyer - they get student hub access by default
        user_role = getattr(user, 'user_role', None)
        is_advocate_or_lawyer = user_role and user_role.role_name in ['advocate', 'lawyer']
        
        return {
            'is_active': False,
            'can_access_legal_library': False,
            'can_ask_questions': False,
            'can_generate_documents': False,
            'can_receive_legal_updates': False,
            'can_access_forum': False,
            'can_access_student_hub': is_advocate_or_lawyer,  # Advocates and lawyers can access student hub
            'can_purchase_consultations': False,
            'can_purchase_documents': False,
            'can_purchase_learning_materials': False,
            # Free Trial restrictions (frontend expected keys)
            'can_comment_forum': False,
            'can_reply_forum': False,
            'can_download_templates': False,
            'can_talk_to_lawyer': False,
            'can_ask_question': False,
            'can_book_consultation': False,
            'legal_education_limit': 0,
            'legal_education_reads': 0,
            'legal_education_remaining': 0,
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


class CanViewTalkToLawyer(BasePermission):
    """
    Permission class for "Talk to Lawyer" page
    Only citizens/students/lecturers can view this page
    Professionals (lawyers) cannot view it as they ARE the service providers
    """
    message = {
        'error': 'Access denied',
        'message': 'This page is for clients seeking legal consultation. As a legal professional, you provide consultations through your profile.',
        'message_sw': 'Ukurasa huu ni kwa wateja wanaotafuta ushauri wa kisheria. Kama mtaalamu wa sheria, unatoa ushauri kupitia wasifu wako.'
    }
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users can view
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check role-based permission
        return check_subscription_permission(request.user, 'can_view_talk_to_lawyer')


class CanViewNearbyLawyers(BasePermission):
    """
    Permission class for viewing nearby lawyers
    Only citizens/students/lecturers with active subscription
    Professionals cannot view nearby lawyers (they are the lawyers!)
    """
    message = {
        'error': 'Access denied',
        'message': 'This feature is for clients seeking legal services. As a legal professional, clients can find you through the platform.',
        'message_sw': 'Kipengele hiki ni kwa wateja wanaotafuta huduma za kisheria. Kama mtaalamu wa sheria, wateja wanaweza kukutafuta kupitia jukwaa.'
    }
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users can view
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check role-based permission
        return check_subscription_permission(request.user, 'can_view_nearby_lawyers')


class IsProfessional(BasePermission):
    """
    Permission class to check if user is a legal professional
    (advocate, lawyer, paralegal, law_firm)
    """
    message = {
        'error': 'Professional account required',
        'message': 'This feature is only available for legal professionals.',
        'message_sw': 'Kipengele hiki kinapatikana tu kwa wataalamu wa sheria.'
    }
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users can access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check if user is a professional
        return is_professional(request.user)


class IsNotProfessional(BasePermission):
    """
    Permission class to check if user is NOT a professional
    Used for features exclusive to citizens/students/lecturers
    """
    message = {
        'error': 'Client account required',
        'message': 'This feature is only available for citizens, students, and lecturers.',
        'message_sw': 'Kipengele hiki kinapatikana tu kwa wananchi, wanafunzi, na wahadhiri.'
    }
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users can access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check if user is NOT a professional
        return not is_professional(request.user)


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


# ============================================================================
# FREE TRIAL RESTRICTION PERMISSION CLASSES
# ============================================================================

class CanCommentInForum(BasePermission):
    """
    Permission class to check if user can comment/reply in forums.
    Free trial users cannot comment - they can only view.
    """
    message = {
        'error': 'Subscription required',
        'message': 'Free trial users can view forums but cannot comment. Please subscribe to participate in discussions.',
        'message_sw': 'Watumiaji wa jaribio bure wanaweza kuona majukwaa lakini hawawezi kutoa maoni. Tafadhali jiandikishe kushiriki katika majadiliano.',
        'upgrade_required': True,
        'restriction': 'forum_comment'
    }
    
    def has_permission(self, request, view):
        # Allow GET requests (viewing)
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Django admin users bypass restrictions
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        return check_subscription_permission(request.user, 'can_comment_forum')


class CanDownloadTemplates(BasePermission):
    """
    Permission class to check if user can download generated templates/documents.
    Free trial users can generate and preview templates but cannot download.
    """
    message = {
        'error': 'Subscription required',
        'message': 'Free trial users can generate and preview documents but cannot download. Please subscribe to download your documents.',
        'message_sw': 'Watumiaji wa jaribio bure wanaweza kutengeneza na kuona nyaraka lakini hawawezi kupakua. Tafadhali jiandikishe kupakua nyaraka zako.',
        'upgrade_required': True,
        'restriction': 'document_download'
    }
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Django admin users bypass restrictions
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        return check_subscription_permission(request.user, 'can_download_templates')


class CanTalkToLawyerFeature(BasePermission):
    """
    Permission class to check if user can access Talk to Lawyer feature.
    Free trial users cannot talk to lawyers.
    """
    message = {
        'error': 'Subscription required',
        'message': 'Free trial users cannot access the Talk to Lawyer feature. Please subscribe to connect with lawyers.',
        'message_sw': 'Watumiaji wa jaribio bure hawawezi kufikia kipengele cha Ongea na Wakili. Tafadhali jiandikishe kuwasiliana na mawakili.',
        'upgrade_required': True,
        'restriction': 'talk_to_lawyer'
    }
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Django admin users bypass restrictions
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        return check_subscription_permission(request.user, 'can_talk_to_lawyer')


class CanAskQuestionQA(BasePermission):
    """
    Permission class to check if user can ask questions in Q&A.
    Free trial users cannot ask questions.
    """
    message = {
        'error': 'Subscription required',
        'message': 'Free trial users cannot ask questions. Please subscribe to get answers to your legal questions.',
        'message_sw': 'Watumiaji wa jaribio bure hawawezi kuuliza maswali. Tafadhali jiandikishe kupata majibu ya maswali yako ya kisheria.',
        'upgrade_required': True,
        'restriction': 'ask_question'
    }
    
    def has_permission(self, request, view):
        # Allow GET requests (viewing questions)
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Django admin users bypass restrictions
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        return check_subscription_permission(request.user, 'can_ask_question')


class CanBookConsultation(BasePermission):
    """
    Permission class to check if user can book consultations.
    Free trial users cannot book consultations.
    """
    message = {
        'error': 'Subscription required',
        'message': 'Free trial users cannot book consultations. Please subscribe to schedule a consultation with a lawyer.',
        'message_sw': 'Watumiaji wa jaribio bure hawawezi kuandikisha ushauri. Tafadhali jiandikishe kupanga ushauri na wakili.',
        'upgrade_required': True,
        'restriction': 'book_consultation'
    }
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Django admin users bypass restrictions
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        return check_subscription_permission(request.user, 'can_book_consultation')


class CanViewLegalEducationContent(BasePermission):
    """
    Permission class to check if user can view legal education subtopics.
    Free trial users are limited to 5 subtopics.
    """
    message = {
        'error': 'Limit reached',
        'message': 'You have reached your free trial limit for legal education content. Please subscribe to continue learning.',
        'message_sw': 'Umefika kikomo chako cha jaribio bure kwa maudhui ya elimu ya kisheria. Tafadhali jiandikishe kuendelea kujifunza.',
        'upgrade_required': True,
        'restriction': 'legal_education_limit'
    }
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Django admin users bypass restrictions
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # This permission just checks if limit is not exhausted
        # Actual subtopic tracking is done in the view
        try:
            subscription = request.user.subscription
            if not subscription.is_active():
                return False
            
            # If unlimited (0), always allow
            if subscription.plan.legal_ed_subtopics_limit == 0:
                return True
            
            # Check if user has remaining views
            return subscription.get_legal_ed_remaining() > 0
        except UserSubscription.DoesNotExist:
            return False


def check_legal_education_access(user, subtopic_id):
    """
    Check if user can access a specific legal education subtopic.
    Tracks the view if allowed.
    
    Args:
        user: PolaUser instance
        subtopic_id: ID of the subtopic being accessed
        
    Returns:
        tuple: (can_access: bool, message: dict or None)
    """
    # Django admin users bypass restrictions
    if user.is_staff or user.is_superuser:
        return (True, None)
    
    try:
        subscription = user.subscription
        if not subscription.is_active():
            return (False, {
                'error': 'Subscription required',
                'message': 'You need an active subscription to access this content.',
                'upgrade_required': True
            })
        
        can_view, reason = subscription.can_view_legal_ed_subtopic(subtopic_id)
        
        if can_view:
            # Track the view
            subscription.track_subtopic_view(subtopic_id)
            return (True, None)
        else:
            return (False, {
                'error': 'Limit reached',
                'message': f'You have viewed {subscription.legal_ed_subtopics_viewed} of {subscription.plan.legal_ed_subtopics_limit} allowed subtopics. Please subscribe to continue.',
                'message_sw': f'Umeona {subscription.legal_ed_subtopics_viewed} kati ya {subscription.plan.legal_ed_subtopics_limit} vichwa vidogo vinavyoruhusiwa. Tafadhali jiandikishe kuendelea.',
                'upgrade_required': True,
                'legal_education_limit': subscription.plan.legal_ed_subtopics_limit,
                'legal_education_reads': subscription.legal_ed_subtopics_viewed,
                'legal_education_remaining': 0
            })
    except UserSubscription.DoesNotExist:
        return (False, {
            'error': 'No subscription',
            'message': 'You need a subscription to access this content.',
            'upgrade_required': True
        })

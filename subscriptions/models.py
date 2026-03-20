from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import timedelta
from authentication.models import PolaUser


# ============================================================================
# SUBSCRIPTION MODELS (Monthly Platform Access - 3,000 TZS)
# ============================================================================

class SubscriptionPlan(models.Model):
    """
    Defines available subscription plans (free trial, monthly, etc.)
    Monthly subscription provides platform access only
    """
    PLAN_TYPES = [
        ('free_trial', 'Free Trial (24 hours)'),
        ('monthly', 'Monthly Subscription'),
    ]
    
    CURRENCY_CHOICES = [
        ('TZS', 'Tanzanian Shilling'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
    ]
    
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    name = models.CharField(max_length=100)
    name_sw = models.CharField(max_length=100, help_text="Swahili name")
    description = models.TextField()
    description_sw = models.TextField(help_text="Swahili description")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='TZS', help_text="Price currency")
    duration_days = models.IntegerField(help_text="Duration in days (1 for trial, 30 for monthly)")
    is_active = models.BooleanField(default=True)
    
    # Features included in this plan
    full_legal_library_access = models.BooleanField(default=False)
    monthly_questions_limit = models.IntegerField(default=0, help_text="0 = unlimited")
    free_documents_per_month = models.IntegerField(default=0)
    legal_updates = models.BooleanField(default=False)
    forum_access = models.BooleanField(default=False)
    student_hub_access = models.BooleanField(default=False)
    
    # Free Trial Restrictions (new fields)
    can_comment_in_forums = models.BooleanField(default=True, help_text="Can user comment/reply in forums and hubs")
    can_download_documents = models.BooleanField(default=True, help_text="Can user download generated documents")
    can_talk_to_lawyer = models.BooleanField(default=True, help_text="Can user access Talk to Lawyer feature")
    can_ask_questions_qa = models.BooleanField(default=True, help_text="Can user ask questions in Q&A")
    can_book_consultation = models.BooleanField(default=True, help_text="Can user book consultations")
    legal_ed_subtopics_limit = models.IntegerField(default=0, help_text="Max subtopics in Legal Education (0 = unlimited)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['price']
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'
    
    def __str__(self):
        currency_symbols = {
            'TZS': 'TSh',
            'USD': '$',
            'EUR': '€',
        }
        symbol = currency_symbols.get(self.currency, self.currency)
        return f"{self.name} - {symbol} {self.price}"
    
    def get_benefits_dict(self, language='en'):
        """Return benefits as dictionary for API responses"""
        benefits = []
        
        # Check if this is a free trial plan
        is_trial = self.plan_type == 'free_trial'
        
        if language == 'sw':
            if is_trial:
                # Free Trial benefits (short phrases)
                benefits.append("Chunguza programu yote")
                benefits.append("Tazama majukwaa (bila maoni)")
                benefits.append("Elimu ya kisheria (mada 5)")
                benefits.append("Tengeneza nyaraka (bila kupakua)")
                benefits.append("Weka akaunti na wasifu")
                # Restrictions
                benefits.append("❌ Huwezi kuongea na wakili")
                benefits.append("❌ Huwezi kuuliza maswali")
                benefits.append("❌ Huwezi kuandikisha ushauri")
            else:
                # Paid subscription benefits
                if self.full_legal_library_access:
                    benefits.append("Maktaba kamili ya kisheria")
                if self.monthly_questions_limit > 0:
                    benefits.append(f"Maswali {self.monthly_questions_limit} kwa mwezi")
                if self.free_documents_per_month > 0:
                    benefits.append(f"Nyaraka {self.free_documents_per_month} bure kwa mwezi")
                if self.legal_updates:
                    benefits.append("Taarifa za kisheria")
                if self.forum_access and self.can_comment_in_forums:
                    benefits.append("Majukwaa kamili (maoni na majibu)")
                if self.student_hub_access:
                    benefits.append("Kituo cha wanafunzi")
                if self.can_talk_to_lawyer:
                    benefits.append("✅ Ongea na wakili")
                if self.can_ask_questions_qa:
                    benefits.append("✅ Uliza maswali")
                if self.can_book_consultation:
                    benefits.append("✅ Andikisha ushauri")
                if self.can_download_documents:
                    benefits.append("✅ Pakua nyaraka")
        else:
            if is_trial:
                # Free Trial benefits (short phrases)
                benefits.append("Full app exploration")
                benefits.append("View forums & hubs (no commenting)")
                benefits.append("Legal education (5 topics)")
                benefits.append("Generate templates (no download)")
                benefits.append("Account & profile setup")
                # Restrictions
                benefits.append("❌ Cannot talk to lawyer")
                benefits.append("❌ Cannot ask questions")
                benefits.append("❌ Cannot book consultation")
            else:
                # Paid subscription benefits
                if self.full_legal_library_access:
                    benefits.append("Full legal library access")
                if self.monthly_questions_limit > 0:
                    benefits.append(f"{self.monthly_questions_limit} questions per month")
                if self.free_documents_per_month > 0:
                    benefits.append(f"{self.free_documents_per_month} free document per month")
                if self.legal_updates:
                    benefits.append("Legal updates & news")
                if self.forum_access and self.can_comment_in_forums:
                    benefits.append("Full forum access (comment & reply)")
                if self.student_hub_access:
                    benefits.append("Student hub access")
                if self.can_talk_to_lawyer:
                    benefits.append("✅ Talk to lawyer")
                if self.can_ask_questions_qa:
                    benefits.append("✅ Ask questions")
                if self.can_book_consultation:
                    benefits.append("✅ Book consultation")
                if self.can_download_documents:
                    benefits.append("✅ Download documents")
        
        return benefits
    
    def get_permissions(self):
        """Return subscription permissions as a dictionary for access control"""
        return {
            'can_access_legal_library': self.full_legal_library_access,
            'can_ask_questions': self.monthly_questions_limit > 0,
            'questions_limit': self.monthly_questions_limit,
            'can_generate_documents': self.free_documents_per_month > 0,
            'free_documents_limit': self.free_documents_per_month,
            'can_receive_legal_updates': self.legal_updates,
            'can_access_forum': self.forum_access,
            'can_access_student_hub': self.student_hub_access,
            'can_purchase_consultations': True,  # All subscribed users can purchase
            'can_purchase_documents': True,  # All subscribed users can purchase
            'can_purchase_learning_materials': True,  # All subscribed users can purchase
            # Free Trial Restrictions (frontend expected keys)
            'can_comment_forum': self.can_comment_in_forums,
            'can_reply_forum': self.can_comment_in_forums,  # Same as comment
            'can_download_templates': self.can_download_documents,
            'can_talk_to_lawyer': self.can_talk_to_lawyer,
            'can_ask_question': self.can_ask_questions_qa,  # Q&A questions
            'can_book_consultation': self.can_book_consultation,
            'legal_education_limit': self.legal_ed_subtopics_limit,
        }


class UserSubscription(models.Model):
    """
    User's active subscription
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending Payment'),
    ]
    
    user = models.OneToOneField(PolaUser, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    
    auto_renew = models.BooleanField(default=False)
    device_id = models.CharField(max_length=255, blank=True, null=True, help_text="Device fingerprint for one-device restriction")
    
    # Usage tracking
    questions_asked_this_month = models.IntegerField(default=0)
    documents_generated_this_month = models.IntegerField(default=0)
    last_reset_date = models.DateField(auto_now_add=True, help_text="Last date monthly limits were reset")
    
    # Free Trial tracking - Legal Education subtopics viewed
    legal_ed_subtopics_viewed = models.IntegerField(default=0, help_text="Number of legal education subtopics viewed (for trial limit)")
    viewed_subtopic_ids = models.JSONField(default=list, blank=True, help_text="List of subtopic IDs user has viewed")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User Subscription'
        verbose_name_plural = 'User Subscriptions'
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status})"
    
    def check_and_update_expired_status(self):
        """
        Check if subscription has expired and update status accordingly.
        Call this method before checking permissions to ensure status is accurate.
        """
        if self.status == 'active' and self.end_date <= timezone.now():
            self.status = 'expired'
            self.save(update_fields=['status', 'updated_at'])
            return True  # Status was updated
        return False  # No change
    
    def is_active(self):
        """Check if subscription is currently active"""
        # First, check and update expired status if needed
        self.check_and_update_expired_status()
        return self.status == 'active' and self.end_date > timezone.now()
    
    def is_trial(self):
        """Check if this is a free trial subscription"""
        return self.plan.plan_type == 'free_trial'
    
    def days_remaining(self):
        """Calculate days remaining in subscription"""
        if self.end_date > timezone.now():
            return (self.end_date - timezone.now()).days
        return 0
    
    def can_ask_question(self):
        """Check if user can ask a question this month"""
        self._reset_monthly_limits_if_needed()
        if self.plan.monthly_questions_limit == 0:  # Unlimited
            return True
        return self.questions_asked_this_month < self.plan.monthly_questions_limit
    
    def can_generate_free_document(self):
        """Check if user can generate a free document this month"""
        self._reset_monthly_limits_if_needed()
        return self.documents_generated_this_month < self.plan.free_documents_per_month
    
    def increment_questions_count(self):
        """Increment questions asked count"""
        self._reset_monthly_limits_if_needed()
        self.questions_asked_this_month += 1
        self.save()
    
    def increment_documents_count(self):
        """Increment documents generated count"""
        self._reset_monthly_limits_if_needed()
        self.documents_generated_this_month += 1
        self.save()
    
    # ========================================================================
    # FREE TRIAL RESTRICTIONS - Legal Education Subtopics
    # ========================================================================
    
    def can_view_legal_ed_subtopic(self, subtopic_id):
        """
        Check if user can view a legal education subtopic.
        
        For free trial users, limited to plan.legal_ed_subtopics_limit subtopics.
        Returns tuple: (can_view: bool, reason: str or None)
        """
        # No limit if plan has 0 (unlimited)
        if self.plan.legal_ed_subtopics_limit == 0:
            return (True, None)
        
        # If user has already viewed this subtopic, allow
        if subtopic_id in (self.viewed_subtopic_ids or []):
            return (True, None)
        
        # Check if limit reached
        if self.legal_ed_subtopics_viewed >= self.plan.legal_ed_subtopics_limit:
            return (False, 'legal_ed_limit_reached')
        
        return (True, None)
    
    def track_subtopic_view(self, subtopic_id):
        """
        Track that user has viewed a subtopic.
        Only counts unique subtopics towards the limit.
        """
        if subtopic_id not in (self.viewed_subtopic_ids or []):
            if self.viewed_subtopic_ids is None:
                self.viewed_subtopic_ids = []
            self.viewed_subtopic_ids.append(subtopic_id)
            self.legal_ed_subtopics_viewed = len(self.viewed_subtopic_ids)
            self.save(update_fields=['viewed_subtopic_ids', 'legal_ed_subtopics_viewed'])
    
    def get_legal_ed_remaining(self):
        """Get remaining legal education subtopics user can view"""
        if self.plan.legal_ed_subtopics_limit == 0:
            return float('inf')
        return max(0, self.plan.legal_ed_subtopics_limit - self.legal_ed_subtopics_viewed)
    
    def can_comment_in_forum(self):
        """Check if user can comment/reply in forums (False for trial users)"""
        return self.plan.can_comment_in_forums
    
    def can_download_document(self):
        """Check if user can download generated documents (False for trial users)"""
        return self.plan.can_download_documents
    
    def can_access_talk_to_lawyer(self):
        """Check if user can access Talk to Lawyer feature (False for trial users)"""
        return self.plan.can_talk_to_lawyer
    
    def can_ask_question_qa(self):
        """Check if user can ask questions in Q&A (False for trial users)"""
        return self.plan.can_ask_questions_qa
    
    def can_book_consultation_service(self):
        """Check if user can book consultations (False for trial users)"""
        return self.plan.can_book_consultation

    def _reset_monthly_limits_if_needed(self):
        """Reset monthly limits if a new month has started"""
        today = timezone.now().date()
        if today.month != self.last_reset_date.month or today.year != self.last_reset_date.year:
            self.questions_asked_this_month = 0
            self.documents_generated_this_month = 0
            self.last_reset_date = today
            self.save()
    
    def extend_subscription(self, days):
        """Extend subscription by specified days (admin only)"""
        self.end_date = self.end_date + timedelta(days=days)
        self.save()
    
    def cancel_subscription(self):
        """Cancel the subscription"""
        self.status = 'cancelled'
        self.auto_renew = False
        self.save()
    
    def activate_subscription(self):
        """Activate the subscription after payment"""
        self.status = 'active'
        if not self.end_date or self.end_date < timezone.now():
            self.end_date = timezone.now() + timedelta(days=self.plan.duration_days)
        self.save()
    
    def get_permissions(self):
        """
        Get subscription permissions for this user
        Combines subscription-based permissions with role-based restrictions
        """
        if not self.is_active():
            return {
                'is_active': False,
                'can_access_legal_library': False,
                'can_ask_questions': False,
                'questions_limit': 0,
                'questions_remaining': 0,
                'can_generate_documents': False,
                'free_documents_limit': 0,
                'documents_remaining': 0,
                'can_receive_legal_updates': False,
                'can_access_forum': False,
                'can_access_student_hub': False,
                'can_purchase_consultations': False,
                'can_purchase_documents': False,
                'can_purchase_learning_materials': False,
                'can_view_talk_to_lawyer': False,
                'can_view_nearby_lawyers': False,
                'can_view_own_consultations': False,
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
        
        # Reset monthly limits if needed
        self._reset_monthly_limits_if_needed()
        
        # Get base permissions from plan
        permissions = self.plan.get_permissions()
        permissions['is_active'] = True
        permissions['is_trial'] = self.is_trial()
        permissions['days_remaining'] = self.days_remaining()
        permissions['end_date'] = self.end_date.isoformat()
        
        # Add usage tracking
        permissions['questions_remaining'] = max(
            0, 
            self.plan.monthly_questions_limit - self.questions_asked_this_month
        ) if self.plan.monthly_questions_limit > 0 else float('inf')
        
        permissions['documents_remaining'] = max(
            0,
            self.plan.free_documents_per_month - self.documents_generated_this_month
        )
        
        # Add Free Trial specific tracking (frontend expected keys)
        permissions['legal_education_reads'] = self.legal_ed_subtopics_viewed
        permissions['legal_education_remaining'] = self.get_legal_ed_remaining()
        
        # Apply role-based restrictions
        user_role = getattr(self.user, 'user_role', None)
        if user_role:
            role_name = user_role.role_name
            professional_roles = ['advocate', 'lawyer', 'paralegal', 'law_firm']
            
            if role_name in professional_roles:
                # PROFESSIONAL RESTRICTIONS
                # Professionals CANNOT view "Talk to Lawyer" page (they ARE the lawyers)
                permissions['can_view_talk_to_lawyer'] = False
                
                # Professionals CANNOT view nearby lawyers (they are the service providers)
                permissions['can_view_nearby_lawyers'] = False
                
                # Professionals CAN still ask questions in Q&A (professional advice exchange)
                # permissions['can_ask_questions'] stays as is from subscription
                
                # Professionals CAN view their OWN consultations (as service providers)
                permissions['can_view_own_consultations'] = True
                
                # Advocates and lawyers can access student hub (to view/mentor students) regardless of subscription
                if role_name in ['advocate', 'lawyer']:
                    permissions['can_access_student_hub'] = True
                
            else:
                # CITIZEN/STUDENT/LECTURER PERMISSIONS
                # These users CAN view Talk to Lawyer page (public page)
                permissions['can_view_talk_to_lawyer'] = True
                
                # These users CAN view nearby lawyers based on subscription
                permissions['can_view_nearby_lawyers'] = permissions['is_active']
                
                # These users CAN view their own consultations as clients
                permissions['can_view_own_consultations'] = True
                
                # Student Hub access is subscription-based (paid users only)
                # Already handled by plan permissions
        else:
            # Default permissions if no role assigned
            permissions['can_view_talk_to_lawyer'] = True
            permissions['can_view_nearby_lawyers'] = permissions['is_active']
            permissions['can_view_own_consultations'] = True
        
        return permissions


# ============================================================================
# CONSULTANT REGISTRATION & APPROVAL MODELS
# ============================================================================

class ConsultantRegistrationRequest(models.Model):
    """
    Consultant registration request - ONLY Law Firms can register as consultants.
    Individual advocates, lawyers, and paralegals cannot be booked directly.
    
    Note: User data (name, email, phone, license numbers, experience, specializations) 
    is already in PolaUser model. This model only stores:
    1. Verification documents (needed for approval)
    2. Service preferences (mobile/physical consultations)
    3. Admin review status
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    CONSULTANT_TYPES = [
        ('law_firm', 'Law Firm'),
        ('advocate', 'Advocate'),
        ('lawyer', 'Lawyer'),
        ('paralegal', 'Paralegal'),
    ]
    
    # User submitting the request (inherits all professional info from PolaUser)
    user = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='consultant_requests')
    consultant_type = models.CharField(max_length=20, choices=CONSULTANT_TYPES)
    
    # Professional Documents (required for verification)
    license_document = models.FileField(
        upload_to='consultant_licenses/', 
        blank=True, 
        null=True,
        help_text="Professional license certificate (if not already in PolaUser documents)"
    )
    id_document = models.FileField(
        upload_to='consultant_ids/',
        blank=True, 
        null=True,
        help_text="National ID or Passport for identity verification"
    )
    cv_document = models.FileField(
        upload_to='consultant_cvs/', 
        blank=True, 
        null=True,
        help_text="Professional CV/Resume"
    )
    additional_documents = models.FileField(
        upload_to='consultant_docs/', 
        blank=True, 
        null=True,
        help_text="Any additional certifications or credentials"
    )
    
    # Service Preferences
    offers_mobile_consultations = models.BooleanField(
        default=True,
        help_text="Willing to provide mobile/video consultations"
    )
    offers_physical_consultations = models.BooleanField(
        default=False,
        help_text="Willing to provide in-person consultations"
    )
    preferred_consultation_city = models.CharField(
        max_length=100,
        blank=True,
        help_text="City for physical consultations (if applicable)"
    )
    
    # Admin Review
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        PolaUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_consultant_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(
        blank=True, 
        help_text="Admin review notes, feedback, or rejection reason"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Consultant Registration Request'
        verbose_name_plural = 'Consultant Registration Requests'
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.consultant_type}) - {self.status}"
    
    def get_professional_info(self):
        """Get professional information from the associated user"""
        return {
            'full_name': self.user.get_full_name(),
            'email': self.user.email,
            'phone': self.user.contact.phone_number if hasattr(self.user, 'contact') else None,
            'years_of_experience': self.user.years_of_experience,
            'specializations': list(self.user.specializations.values_list('name_en', flat=True)),
            'roll_number': self.user.roll_number,
            'bar_membership_number': self.user.bar_membership_number,
        }
    
    def approve(self, admin_user):
        """Approve the request and create ConsultantProfile"""
        self.status = 'approved'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()
        
        # Get specializations as comma-separated string
        specializations = ', '.join(self.user.specializations.values_list('name_en', flat=True))
        
        # Create ConsultantProfile (using data from PolaUser + request preferences)
        ConsultantProfile.objects.create(
            user=self.user,
            registration_request=self,
            consultant_type=self.consultant_type,
            specialization=specializations or 'General Practice',
            years_of_experience=self.user.years_of_experience or 0,
            offers_mobile_consultations=self.offers_mobile_consultations,
            offers_physical_consultations=self.offers_physical_consultations,
            city=self.preferred_consultation_city or '',
            is_available=True
        )
    
    def reject(self, admin_user, reason):
        """Reject the request"""
        self.status = 'rejected'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.admin_notes = reason
        self.save()



class ConsultantProfile(models.Model):
    """
    Active consultant profile - created after approval.
    Only Law Firms can have consultant profiles and be booked.
    Individual advocates, lawyers, and paralegals cannot be booked directly.
    """
    CONSULTANT_TYPES = [
        ('law_firm', 'Law Firm'),
        ('advocate', 'Advocate'),
        ('lawyer', 'Lawyer'),
        ('paralegal', 'Paralegal'),
    ]
    
    user = models.OneToOneField(PolaUser, on_delete=models.CASCADE, related_name='consultant_profile')
    registration_request = models.OneToOneField(
        ConsultantRegistrationRequest, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='approved_profile'
    )
    
    consultant_type = models.CharField(max_length=20, choices=CONSULTANT_TYPES)
    specialization = models.TextField()
    years_of_experience = models.IntegerField()
    
    # Service Offerings
    offers_mobile_consultations = models.BooleanField(default=True)
    offers_physical_consultations = models.BooleanField(default=False)
    city = models.CharField(max_length=100, blank=True)
    
    # Availability
    is_available = models.BooleanField(default=True, help_text="Currently accepting consultations")
    
    # Stats
    total_consultations = models.IntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0'), validators=[MinValueValidator(Decimal('0'))])
    total_reviews = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-average_rating', '-total_consultations']
        verbose_name = 'Consultant Profile'
        verbose_name_plural = 'Consultant Profiles'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.consultant_type}"
    
    def get_pricing(self):
        """Get pricing for law firm consultations"""
        try:
            pricing = {}
            
            # Mobile consultation pricing (50/50 split)
            if self.offers_mobile_consultations:
                # Use MOBILE_LAW_FIRM as the default pricing for now, 
                # or match specifically if needed.
                service_type = 'MOBILE_LAW_FIRM'
                
                # Check for specific deprecated types if we want to be backward compatible
                # but MOBILE_LAW_FIRM is the current standard.
                
                mobile_pricing = PricingConfiguration.objects.get(
                    service_type=service_type,
                    is_active=True
                )
                pricing['mobile'] = {
                    'price': mobile_pricing.price,
                    'consultant_share': mobile_pricing.consultant_share_percent,
                    'platform_share': mobile_pricing.platform_commission_percent,
                }
            
            # Physical consultation pricing (60/40 split) - Law Firm only
            if self.offers_physical_consultations:
                physical_pricing = PricingConfiguration.objects.get(
                    service_type='PHYSICAL_LAW_FIRM',
                    is_active=True
                )
                pricing['physical'] = {
                    'price': physical_pricing.price,
                    'consultant_share': physical_pricing.consultant_share_percent,
                    'platform_share': physical_pricing.platform_commission_percent,
                }
            
            return pricing
        except PricingConfiguration.DoesNotExist:
            return {}


# ============================================================================
# PRICING CONFIGURATION (Pay-Per-Use Services)
# ============================================================================

class PricingConfiguration(models.Model):
    """
    Centralized pricing for all pay-per-use services
    Separate from monthly subscription (SubscriptionPlan)
    
    Revenue Splits:
    - Mobile consultations: 50/50 (App/Law Firm)
    - Physical consultations: 60/40 (App/Law Firm)
    - Student materials: 50/50 (App/Uploader)
    - Lecturer materials: 40/60 (App/Uploader)
    - Admin materials: 100/0 (App/Uploader)
    
    NOTE: Only Law Firms can be booked as consultants.
    Individual advocates, lawyers, and paralegals cannot be booked directly.
    """
    SERVICE_TYPES = [
        # Law Firm Consultations - Mobile (50/50 split)
        ('MOBILE_LAW_FIRM', 'Mobile Consultation - Law Firm (In-App Call)'),
        
        # Law Firm Consultations - Physical (60/40 split)
        ('PHYSICAL_LAW_FIRM', 'Physical Consultation - Law Firm'),
        
        # Legacy types (kept for backward compatibility - may be removed)
        ('MOBILE_ADVOCATE', 'Mobile Consultation - Advocate (DEPRECATED)'),
        ('MOBILE_LAWYER', 'Mobile Consultation - Lawyer (DEPRECATED)'),
        ('MOBILE_PARALEGAL', 'Mobile Consultation - Paralegal (DEPRECATED)'),
        ('PHYSICAL_ADVOCATE', 'Physical Consultation - Advocate (DEPRECATED)'),
        ('PHYSICAL_LAWYER', 'Physical Consultation - Lawyer (DEPRECATED)'),
        ('PHYSICAL_PARALEGAL', 'Physical Consultation - Paralegal (DEPRECATED)'),
        
        # Documents
        ('DOCUMENT_STANDARD', 'Standard Document Generation'),
        ('DOCUMENT_ADVANCED', 'Advanced Document Generation'),
        
        # Learning Materials
        ('MATERIAL_STUDENT', 'Study Material - Student Upload'),
        ('MATERIAL_LECTURER', 'Study Material - Lecturer Upload'),
        ('MATERIAL_ADMIN', 'Study Material - Admin Upload'),
    ]
    
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    
    # Revenue Split (varies by service type)
    platform_commission_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('50.00'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Platform commission percentage (50% for mobile, 60% for physical, varies for materials)"
    )
    consultant_share_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('50.00'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Consultant/Uploader share percentage (50% for mobile, 40% for physical, varies for materials)"
    )
    
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['service_type']
        verbose_name = 'Pricing Configuration'
        verbose_name_plural = 'Pricing Configurations'
    
    def __str__(self):
        return f"{self.get_service_type_display()} - {self.price} TZS"
    
    def calculate_split(self):
        """Calculate revenue split amounts"""
        platform_amount = (self.price * self.platform_commission_percent) / 100
        consultant_amount = (self.price * self.consultant_share_percent) / 100
        return {
            'platform': platform_amount,
            'consultant': consultant_amount,
            'total': self.price
        }


# ============================================================================
# CALL CREDITS & CONSULTATION BOOKINGS
# ============================================================================

class CallCreditBundle(models.Model):
    """
    Call credit bundles for mobile consultations (Consultation Vouchers)
    
    Pricing Tiers:
    - BRONZE/SHABA: 5 min = 3,000 TZS (3 days expiry; carry forward unused minutes within 3 days)
    - SILVER/FEDHA: 10 min = 5,000 TZS (5 days expiry; carry forward unused minutes within 5 days)
    - GOLD/DHAHABU: 20 min = 9,000 TZS (7 days expiry; carry forward unused minutes within 7 days)
    """
    CURRENCY_CHOICES = [
        ('TZS', 'Tanzanian Shilling'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
    ]
    
    name = models.CharField(max_length=100, help_text="English name")
    name_sw = models.CharField(max_length=100, blank=True, help_text="Swahili name")
    description = models.TextField(blank=True, help_text="English description of the bundle")
    description_sw = models.TextField(blank=True, help_text="Swahili description of the bundle")
    minutes = models.IntegerField(help_text="Total minutes in bundle")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='TZS', help_text="Price currency")
    validity_days = models.IntegerField(help_text="Days until expiry after purchase (carry forward period)")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['price']
        verbose_name = 'Call Credit Bundle (Consultation Voucher)'
        verbose_name_plural = 'Call Credit Bundles (Consultation Vouchers)'
    
    def __str__(self):
        currency_symbols = {'TZS': 'TSh', 'USD': '$', 'EUR': '€'}
        symbol = currency_symbols.get(self.currency, self.currency)
        return f"{self.name} - {self.minutes} minutes - {symbol} {self.price} ({self.validity_days} days)"


class UserCallCredit(models.Model):
    """
    User's available call credits
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('depleted', 'Fully Used'),
    ]
    
    user = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='call_credits')
    bundle = models.ForeignKey(CallCreditBundle, on_delete=models.PROTECT)
    
    total_minutes = models.IntegerField()
    remaining_minutes = models.IntegerField()
    
    purchase_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    class Meta:
        ordering = ['expiry_date']
        verbose_name = 'User Call Credit'
        verbose_name_plural = 'User Call Credits'
    
    def __str__(self):
        return f"{self.user.email} - {self.remaining_minutes}/{self.total_minutes} mins"
    
    def is_valid(self):
        """Check if credit is still valid"""
        if self.status != 'active':
            return False
        if self.expiry_date < timezone.now():
            self.status = 'expired'
            self.save()
            return False
        if self.remaining_minutes <= 0:
            self.status = 'depleted'
            self.save()
            return False
        return True
    
    def deduct_minutes(self, minutes):
        """Deduct minutes from credit"""
        if not self.is_valid():
            raise ValueError("Credit is not valid")
        if self.remaining_minutes < minutes:
            raise ValueError("Insufficient minutes")
        
        self.remaining_minutes -= minutes
        if self.remaining_minutes == 0:
            self.status = 'depleted'
        self.save()


class ConsultationBooking(models.Model):
    """
    Physical Consultation Booking - ONLY for in-person meetings with Law Firms.
    Mobile consultations are handled separately via CallSession/CallCredits.
    
    NOTE: Only verified Law Firms can be booked for physical consultations.
    Individual advocates, lawyers, and paralegals cannot be booked directly.
    """
    BOOKING_TYPES = [
        ('physical', 'Physical Consultation'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    # Participants
    client = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='consultation_bookings')
    consultant = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='consultant_bookings')
    
    booking_type = models.CharField(max_length=20, choices=BOOKING_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Scheduling
    scheduled_date = models.DateTimeField()
    scheduled_duration_minutes = models.IntegerField(default=30)
    
    # Actual session times
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    actual_duration_minutes = models.IntegerField(default=0)
    
    # Pricing
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform_commission = models.DecimalField(max_digits=10, decimal_places=2)
    consultant_earnings = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Physical consultation details
    meeting_location = models.TextField(blank=True, help_text="For physical consultations")
    
    # Notes
    client_notes = models.TextField(blank=True, help_text="Client's consultation topic/questions")
    consultant_notes = models.TextField(blank=True, help_text="Consultant's session notes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_date']
        verbose_name = 'Consultation Booking'
        verbose_name_plural = 'Consultation Bookings'
    
    def __str__(self):
        return f"{self.client.email} with {self.consultant.email} - {self.scheduled_date}"
    
    def confirm_booking(self):
        """Confirm the booking"""
        self.status = 'confirmed'
        self.save()
    
    def start_session(self):
        """Start the consultation session"""
        self.status = 'in_progress'
        self.actual_start_time = timezone.now()
        self.save()
    
    def complete_session(self):
        """Complete the session and process payments"""
        self.status = 'completed'
        self.actual_end_time = timezone.now()
        
        if self.actual_start_time:
            self.actual_duration_minutes = int(
                (self.actual_end_time - self.actual_start_time).total_seconds() / 60
            )
        
        self.save()
        
        # Record consultant earnings
        ConsultantEarnings.objects.create(
            consultant=self.consultant,
            booking=self,
            service_type=f"{self.booking_type}_consultation",
            gross_amount=self.total_amount,
            platform_commission=self.platform_commission,
            net_earnings=self.consultant_earnings
        )
        
        # Update consultant stats
        if hasattr(self.consultant, 'consultant_profile'):
            profile = self.consultant.consultant_profile
            profile.total_consultations += 1
            profile.total_earnings += self.consultant_earnings
            profile.save()


class ConsultantReview(models.Model):
    """
    Client reviews and ratings for consultants after completed consultations
    """
    consultant = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='consultant_reviews')
    client = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='client_reviews')
    booking = models.OneToOneField(ConsultationBooking, on_delete=models.CASCADE, related_name='review')
    
    # Rating (1-5 stars)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    
    # Review details
    review_text = models.TextField(blank=True, help_text="Client's written review")
    
    # Specific ratings (optional, for detailed feedback)
    professionalism_rating = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Professionalism rating"
    )
    communication_rating = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Communication clarity rating"
    )
    expertise_rating = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Legal expertise rating"
    )
    
    # Response from consultant (optional)
    consultant_response = models.TextField(blank=True, help_text="Consultant's response to review")
    response_date = models.DateTimeField(null=True, blank=True)
    
    # Moderation
    is_visible = models.BooleanField(default=True, help_text="Show/hide review")
    flagged = models.BooleanField(default=False, help_text="Flagged for moderation")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Consultant Review'
        verbose_name_plural = 'Consultant Reviews'
        unique_together = ['booking', 'client']  # One review per booking per client
    
    def __str__(self):
        return f"{self.client.email} reviewed {self.consultant.email} - {self.rating} stars"
    
    def save(self, *args, **kwargs):
        """Update consultant's average rating when review is saved"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Update consultant profile ratings
        if hasattr(self.consultant, 'consultant_profile'):
            profile = self.consultant.consultant_profile
            
            # Recalculate average rating
            from django.db.models import Avg, Count
            stats = ConsultantReview.objects.filter(
                consultant=self.consultant,
                is_visible=True
            ).aggregate(
                avg_rating=Avg('rating'),
                total_reviews=Count('id')
            )
            
            profile.average_rating = stats['avg_rating'] or Decimal('0')
            profile.total_reviews = stats['total_reviews'] or 0
            profile.save()


class CallSession(models.Model):
    """
    Individual call sessions within a consultation
    Handles incoming call flow: initiate → ringing → accept/reject → active → completed
    """
    CALL_STATUS_CHOICES = [
        ('ringing', 'Ringing'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('missed', 'Missed'),
        ('cancelled', 'Cancelled'),
    ]
    
    CALL_TYPE_CHOICES = [
        ('voice', 'Voice Call'),
        ('video', 'Video Call'),
    ]
    
    ENDED_BY_CHOICES = [
        ('user', 'User'),
        ('consultant', 'Consultant'),
        ('system', 'System'),
    ]
    
    # Consultation linking (optional - for consultations booked in advance)
    booking = models.ForeignKey(ConsultationBooking, on_delete=models.CASCADE, related_name='call_sessions', null=True, blank=True)
    
    # Direct call participants (for instant calls without booking)
    caller = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='initiated_calls', null=True, blank=True, help_text="User who initiated the call")
    consultant = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='received_calls', null=True, blank=True, help_text="Consultant receiving the call")
    
    # Call details
    channel_name = models.CharField(max_length=255, null=True, blank=True, help_text="Agora channel name")
    call_type = models.CharField(max_length=20, choices=CALL_TYPE_CHOICES, default='voice')
    status = models.CharField(max_length=50, choices=CALL_STATUS_CHOICES, default='ringing')
    
    # Timestamps
    initiated_at = models.DateTimeField(null=True, blank=True, help_text="When call was initiated")
    accepted_at = models.DateTimeField(null=True, blank=True, help_text="When consultant accepted")
    ended_at = models.DateTimeField(null=True, blank=True, help_text="When call ended")
    
    # Legacy fields (for backward compatibility)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=0)
    
    # Call termination
    ended_by = models.CharField(max_length=20, choices=ENDED_BY_CHOICES, null=True, blank=True)
    
    # Credits and billing
    call_credit = models.ForeignKey(UserCallCredit, on_delete=models.SET_NULL, null=True, blank=True)
    credits_deducted = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Call quality
    call_quality_rating = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-initiated_at']
        verbose_name = 'Call Session'
        verbose_name_plural = 'Call Sessions'
        indexes = [
            models.Index(fields=['caller', 'status']),
            models.Index(fields=['consultant', 'status']),
            models.Index(fields=['channel_name']),
            models.Index(fields=['status', 'initiated_at']),
        ]
    
    def __str__(self):
        return f"Call: {self.caller.email} → {self.consultant.email} ({self.status})"
    
    def accept_call(self):
        """Consultant accepts the call"""
        self.status = 'active'
        self.accepted_at = timezone.now()
        self.start_time = self.accepted_at  # For backward compatibility
        self.save()
    
    def reject_call(self):
        """Consultant rejects the call"""
        self.status = 'rejected'
        self.ended_at = timezone.now()
        self.save()
    
    def mark_as_missed(self):
        """Mark call as missed if not answered within timeout"""
        self.status = 'missed'
        self.ended_at = timezone.now()
        self.save()
    
    def end_call(self, ended_by='user', duration_seconds=None):
        """End the call and deduct minutes (rounds up to nearest minute)"""
        import math
        
        self.status = 'completed'
        self.ended_at = timezone.now()
        self.end_time = self.ended_at  # For backward compatibility
        self.ended_by = ended_by
        
        # Calculate duration in seconds
        if duration_seconds:
            actual_seconds = duration_seconds
        elif self.accepted_at:
            actual_seconds = (self.ended_at - self.accepted_at).total_seconds()
        else:
            actual_seconds = 0
        
        # Round UP to nearest minute (e.g., 61 seconds = 2 minutes)
        self.duration_minutes = math.ceil(actual_seconds / 60) if actual_seconds > 0 else 0
        
        self.save()
        
        # Deduct from call credit if available
        if self.call_credit and self.duration_minutes > 0:
            try:
                if self.call_credit.is_valid():
                    # Check if user has enough credits
                    if self.call_credit.remaining_minutes >= self.duration_minutes:
                        self.call_credit.deduct_minutes(self.duration_minutes)
                        self.credits_deducted = Decimal(str(self.duration_minutes))
                    else:
                        # Deduct whatever is available
                        available = self.call_credit.remaining_minutes
                        self.call_credit.deduct_minutes(available)
                        self.credits_deducted = Decimal(str(available))
                    self.save()
            except Exception as e:
                # Log error but don't fail the call end
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error deducting credits: {e}")
    
    def get_duration_seconds(self):
        """Get call duration in seconds"""
        if self.ended_at and self.accepted_at:
            return int((self.ended_at - self.accepted_at).total_seconds())
        return 0


# ============================================================================
# EARNINGS TRACKING
# ============================================================================

class ConsultantEarnings(models.Model):
    """
    Track consultant earnings from consultations
    """
    consultant = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='consultant_earnings')
    booking = models.ForeignKey(ConsultationBooking, on_delete=models.CASCADE, related_name='earnings_record')
    
    service_type = models.CharField(max_length=50)
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total booking amount")
    platform_commission = models.DecimalField(max_digits=10, decimal_places=2, help_text="Platform's share (60%)")
    net_earnings = models.DecimalField(max_digits=10, decimal_places=2, help_text="Consultant's share (40%)")
    
    paid_out = models.BooleanField(default=False)
    payout_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Consultant Earnings'
        verbose_name_plural = 'Consultant Earnings'
    
    def __str__(self):
        return f"{self.consultant.email} - {self.net_earnings} TZS from {self.booking}"


class UploaderEarnings(models.Model):
    """
    Track uploader earnings from materials/documents
    """
    uploader = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='uploader_earnings')
    material = models.ForeignKey('documents.LearningMaterial', on_delete=models.CASCADE, null=True, blank=True)
    
    service_type = models.CharField(max_length=50)
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform_commission = models.DecimalField(max_digits=10, decimal_places=2)
    net_earnings = models.DecimalField(max_digits=10, decimal_places=2)
    
    paid_out = models.BooleanField(default=False)
    payout_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Uploader Earnings'
        verbose_name_plural = 'Uploader Earnings'
    
    def __str__(self):
        return f"{self.uploader.email} - {self.net_earnings} TZS"


class Disbursement(models.Model):
    """
    Track manual disbursements/payouts to consultants and uploaders
    Admin-initiated payments for earnings withdrawal
    """
    DISBURSEMENT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    DISBURSEMENT_TYPE = [
        ('consultant', 'Consultant Earnings'),
        ('uploader', 'Uploader Earnings'),
        ('refund', 'Refund'),
        ('other', 'Other'),
    ]
    
    PAYMENT_METHOD = [
        ('tigo_pesa', 'Tigo Pesa'),
        ('airtel_money', 'Airtel Money'),
        ('mpesa', 'M-Pesa'),
        ('halopesa', 'Halopesa'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    # Recipient information
    recipient = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='disbursements')
    recipient_phone = models.CharField(max_length=15, help_text="Phone number for mobile money (255XXXXXXXXX)")
    recipient_name = models.CharField(max_length=255, blank=True)
    
    # Bank details (for bank transfers)
    bank_account_number = models.CharField(max_length=50, blank=True, null=True, help_text="Bank account number")
    bank_code = models.CharField(max_length=20, blank=True, null=True, help_text="Bank code/SWIFT code")
    bank_name = models.CharField(max_length=100, blank=True, null=True, help_text="Bank name")
    account_verified = models.BooleanField(default=False, help_text="Whether account was verified via name inquiry")
    
    # Disbursement details
    disbursement_type = models.CharField(max_length=20, choices=DISBURSEMENT_TYPE, default='consultant')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('1000'))])
    currency = models.CharField(max_length=3, default='TZS')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD)
    
    # Transaction tracking
    azampay_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    external_reference = models.CharField(max_length=255, unique=True, help_text="Internal reference ID")
    status = models.CharField(max_length=20, choices=DISBURSEMENT_STATUS, default='pending')
    
    # Related earnings (if applicable)
    consultant_earnings = models.ManyToManyField('ConsultantEarnings', blank=True, related_name='disbursements')
    uploader_earnings = models.ManyToManyField('UploaderEarnings', blank=True, related_name='disbursements')
    
    # Admin details
    initiated_by = models.ForeignKey(PolaUser, on_delete=models.SET_NULL, null=True, related_name='initiated_disbursements')
    notes = models.TextField(blank=True, help_text="Admin notes")
    failure_reason = models.TextField(blank=True, help_text="Reason for failure if status is failed")
    
    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-initiated_at']
        verbose_name = 'Disbursement'
        verbose_name_plural = 'Disbursements'
        indexes = [
            models.Index(fields=['-initiated_at']),
            models.Index(fields=['status']),
            models.Index(fields=['recipient', '-initiated_at']),
        ]
    
    def __str__(self):
        return f"Disbursement {self.external_reference} - {self.amount} TZS to {self.recipient.email}"
    
    def save(self, *args, **kwargs):
        # Auto-generate external reference if not provided
        if not self.external_reference:
            import uuid
            timestamp = int(timezone.now().timestamp())
            self.external_reference = f"DISB_{timestamp}_{uuid.uuid4().hex[:8].upper()}"
        
        # Set recipient name if not provided
        if not self.recipient_name:
            if hasattr(self.recipient, 'full_name') and callable(self.recipient.full_name):
                full_name = self.recipient.full_name().strip()
                # Use full name if available, otherwise use email
                self.recipient_name = full_name if full_name else self.recipient.email
            else:
                self.recipient_name = self.recipient.email
        
        super().save(*args, **kwargs)
    
    def mark_completed(self, transaction_id: str = None):
        """Mark disbursement as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if transaction_id:
            self.azampay_transaction_id = transaction_id
        self.save()
        
        # Mark related earnings as paid out
        if self.disbursement_type == 'consultant':
            self.consultant_earnings.update(paid_out=True, payout_date=timezone.now())
        elif self.disbursement_type == 'uploader':
            self.uploader_earnings.update(paid_out=True, payout_date=timezone.now())
    
    def mark_failed(self, reason: str):
        """Mark disbursement as failed"""
        self.status = 'failed'
        self.failure_reason = reason
        self.processed_at = timezone.now()
        self.save()


# ============================================================================
# DOCUMENT GENERATION & PURCHASES
# ============================================================================

class GeneratedDocument(models.Model):
    """
    Legal documents generated by the system
    """
    DOCUMENT_TYPES = [
        ('affidavit', 'Affidavit'),
        ('contract', 'Contract'),
        ('agreement', 'Agreement'),
        ('petition', 'Petition'),
        ('notice', 'Notice'),
        ('letter', 'Legal Letter'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='generated_docs')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=255)
    
    # Document content
    template_used = models.CharField(max_length=255, blank=True)
    document_data = models.JSONField(help_text="Data used to generate document")
    generated_file = models.FileField(upload_to='generated_documents/')
    
    # Pricing
    was_free = models.BooleanField(default=False, help_text="Used monthly free document quota")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Generated Document'
        verbose_name_plural = 'Generated Documents'
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"


class GeneratedDocumentPurchase(models.Model):
    """
    Track purchases of generated documents (if not free)
    """
    user = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='document_purchases')
    document = models.ForeignKey(GeneratedDocument, on_delete=models.CASCADE, related_name='purchases')
    
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Generated Document Purchase'
        verbose_name_plural = 'Generated Document Purchases'
    
    def __str__(self):
        return f"{self.user.email} - {self.document.title}"


class MaterialPurchase(models.Model):
    """
    Track study material purchases
    """
    buyer = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='material_purchases')
    material = models.ForeignKey('documents.LearningMaterial', on_delete=models.CASCADE, related_name='material_purchases')
    
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    platform_commission = models.DecimalField(max_digits=10, decimal_places=2)
    uploader_earnings = models.DecimalField(max_digits=10, decimal_places=2)
    
    download_count = models.IntegerField(default=0)
    last_downloaded = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Material Purchase'
        verbose_name_plural = 'Material Purchases'
        unique_together = ['buyer', 'material']
    
    def __str__(self):
        return f"{self.buyer.email} - {self.material.title}"


# ============================================================================
# PAYMENT TRANSACTIONS (Replaces Wallet System)
# ============================================================================

class PaymentTransaction(models.Model):
    """
    All payment transactions - subscriptions, consultations, documents, materials
    Direct payment via AzamPay (no wallet)
    """
    TRANSACTION_TYPES = [
        ('subscription', 'Subscription Payment'),
        ('consultation', 'Consultation Payment'),
        ('document', 'Document Purchase'),
        ('material', 'Study Material Purchase'),
        ('call_credit', 'Call Credit Purchase'),
        ('refund', 'Refund'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHODS = [
        ('azampay', 'AzamPay'),
        ('mpesa', 'M-Pesa'),
        ('tigopesa', 'Tigo Pesa'),
        ('card', 'Card Payment'),
        ('bank', 'Bank Transfer'),
    ]
    
    user = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='payment_transactions')
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='TZS')
    
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    payment_reference = models.CharField(max_length=255, unique=True)
    gateway_reference = models.CharField(max_length=255, blank=True, help_text="Reference from payment gateway")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Related objects (polymorphic relations for different payment types)
    related_subscription = models.ForeignKey(UserSubscription, on_delete=models.SET_NULL, null=True, blank=True)
    related_booking = models.ForeignKey(ConsultationBooking, on_delete=models.SET_NULL, null=True, blank=True)
    related_call_credit = models.ForeignKey(UserCallCredit, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_transactions')
    related_document = models.ForeignKey(GeneratedDocument, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_transactions')
    related_material = models.ForeignKey('documents.LearningMaterial', on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_transactions')
    
    # Item metadata (store details for API responses)
    item_metadata = models.JSONField(default=dict, blank=True, help_text="Store item details (plan name, bundle info, document title, etc.)")
    
    # Fulfillment tracking
    is_fulfilled = models.BooleanField(default=False, help_text="Has the purchase been delivered/activated?")
    fulfilled_at = models.DateTimeField(null=True, blank=True)
    fulfillment_notes = models.TextField(blank=True)
    
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment Transaction'
        verbose_name_plural = 'Payment Transactions'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['payment_reference']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.amount} TZS - {self.status}"
    
    def mark_completed(self):
        """Mark transaction as completed"""
        self.status = 'completed'
        self.save()
    
    def mark_failed(self):
        """Mark transaction as failed"""
        self.status = 'failed'
        self.save()
    
    def mark_fulfilled(self, notes=''):
        """Mark transaction as fulfilled"""
        self.is_fulfilled = True
        self.fulfilled_at = timezone.now()
        if notes:
            self.fulfillment_notes = notes
        self.save()
    
    def get_related_item(self):
        """Get the related purchase item based on transaction_type"""
        type_mapping = {
            'subscription': 'related_subscription',
            'consultation': 'related_booking',
            'call_credit': 'related_call_credit',
            'document': 'related_document',
            'material': 'related_material',
        }
        field_name = type_mapping.get(self.transaction_type)
        if field_name:
            return getattr(self, field_name, None)
        return None


# ============================================================================
# EXISTING MODELS (Keep for backward compatibility - will deprecate later)
# ============================================================================

class ConsultationVoucher(models.Model):
    """
    Consultation vouchers purchased by users
    NOTE: Being replaced by ConsultationBooking model
    """
    VOUCHER_TYPES = [
        ('mobile', 'Mobile Consultation (In-App Call)'),
        ('physical', 'Physical Consultation'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('used', 'Fully Used'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='consultation_vouchers')
    voucher_type = models.CharField(max_length=20, choices=VOUCHER_TYPES)
    
    # Duration and pricing
    duration_minutes = models.IntegerField(help_text="Total minutes purchased")
    remaining_minutes = models.IntegerField(help_text="Remaining unused minutes")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Expiry
    purchase_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Usage tracking
    sessions_count = models.IntegerField(default=0, help_text="Number of sessions this voucher was used for")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Consultation Voucher'
        verbose_name_plural = 'Consultation Vouchers'
    
    def __str__(self):
        return f"{self.user.email} - {self.duration_minutes}min ({self.voucher_type})"
    
    def is_active(self):
        """Check if voucher is active and not expired"""
        if self.status != 'active':
            return False
        if self.expiry_date < timezone.now():
            self.status = 'expired'
            self.save()
            return False
        if self.remaining_minutes <= 0:
            self.status = 'used'
            self.save()
            return False
        return True
    
    def use_minutes(self, minutes):
        """Deduct minutes from voucher"""
        if not self.is_active():
            raise ValueError("Voucher is not active")
        
        if self.remaining_minutes < minutes:
            raise ValueError(f"Insufficient minutes. Only {self.remaining_minutes} minutes remaining")
        
        self.remaining_minutes -= minutes
        self.sessions_count += 1
        
        if self.remaining_minutes == 0:
            self.status = 'used'
        
        self.save()


class DocumentType(models.Model):
    """
    Types of legal documents available
    """
    DOCUMENT_CATEGORIES = [
        ('standard', 'Standard Document'),
        ('advanced', 'Advanced Document'),
    ]
    
    category = models.CharField(max_length=20, choices=DOCUMENT_CATEGORIES)
    name = models.CharField(max_length=200)
    name_sw = models.CharField(max_length=200, help_text="Swahili name")
    description = models.TextField()
    description_sw = models.TextField(help_text="Swahili description")
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Template information
    template_path = models.CharField(max_length=255, blank=True, help_text="Path to document template")
    required_fields = models.JSONField(default=dict, help_text="Fields required to generate this document")
    
    is_active = models.BooleanField(default=True)
    downloads_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Document Type'
        verbose_name_plural = 'Document Types'
    
    def __str__(self):
        return f"{self.name} ({self.category}) - {self.price} TZS"
    
    def increment_downloads(self):
        """Increment download count"""
        self.downloads_count += 1
        self.save()


class DocumentPurchase(models.Model):
    """
    User's purchased/generated documents
    NOTE: Being replaced by GeneratedDocumentPurchase
    """
    user = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='purchased_documents')
    document_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT, related_name='purchases')
    
    # Purchase details
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    was_free = models.BooleanField(default=False, help_text="True if used monthly free document")
    
    # Generated document
    generated_file = models.FileField(upload_to='generated_documents/', blank=True, null=True)
    document_data = models.JSONField(default=dict, help_text="Data used to generate the document")
    
    # Download tracking
    download_count = models.IntegerField(default=0)
    last_downloaded = models.DateTimeField(null=True, blank=True)
    
    purchase_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-purchase_date']
        verbose_name = 'Document Purchase'
        verbose_name_plural = 'Document Purchases'
    
    def __str__(self):
        return f"{self.user.email} - {self.document_type.name}"
    
    def increment_download(self):
        """Increment download count"""
        self.download_count += 1
        self.last_downloaded = timezone.now()
        self.save()


# ============================================================================
# NOTE: LearningMaterial and LearningMaterialPurchase have been moved to
# the 'documents' app for better separation of concerns.
# Import them from documents.models if needed.
# ============================================================================

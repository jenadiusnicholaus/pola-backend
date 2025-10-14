from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import timedelta
from authentication.models import PolaUser


class SubscriptionPlan(models.Model):
    """
    Defines available subscription plans (free trial, monthly, etc.)
    """
    PLAN_TYPES = [
        ('free_trial', 'Free Trial (24 hours)'),
        ('monthly', 'Monthly Subscription'),
    ]
    
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    name = models.CharField(max_length=100)
    name_sw = models.CharField(max_length=100, help_text="Swahili name")
    description = models.TextField()
    description_sw = models.TextField(help_text="Swahili description")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    duration_days = models.IntegerField(help_text="Duration in days (1 for trial, 30 for monthly)")
    is_active = models.BooleanField(default=True)
    
    # Features included in this plan
    full_legal_library_access = models.BooleanField(default=False)
    monthly_questions_limit = models.IntegerField(default=0, help_text="0 = unlimited")
    free_documents_per_month = models.IntegerField(default=0)
    legal_updates = models.BooleanField(default=False)
    forum_access = models.BooleanField(default=False)
    student_hub_access = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['price']
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'
    
    def __str__(self):
        return f"{self.name} - {self.price} TZS"
    
    def get_benefits_dict(self, language='en'):
        """Return benefits as dictionary for API responses"""
        benefits = []
        
        if language == 'sw':
            if self.full_legal_library_access:
                benefits.append("Pata taarifa, elimu na nyaraka za kisheria bila kikomo")
            if self.monthly_questions_limit > 0:
                benefits.append(f"Pata Msaada wa Kisheria bila Malipo kwa kuuliza maswali hadi {self.monthly_questions_limit} ya kisheria kila mwezi")
            if self.free_documents_per_month > 0:
                benefits.append(f"Tengeneza na pakua nyaraka {self.free_documents_per_month} ya kisheria ya kibinafsi BURE kila mwezi")
            if self.legal_updates:
                benefits.append("Pokea taarifa, habari na Ushauri wa kisheria mara kwa mara")
            if self.forum_access:
                benefits.append("Ungana na watumiaji wengine na jadili mada za kisheria kwenye majukwaa husika")
            if self.student_hub_access:
                benefits.append("Ungana na wanafunzi wenzako kutoka vyuo tofauti, shiriki majadiliano, notes za masomo, mitihani ya awali, na nyaraka nyingine muhimu za kusaidia masomo yako")
        else:
            if self.full_legal_library_access:
                benefits.append("Enjoy full access to legal knowledge library")
            if self.monthly_questions_limit > 0:
                benefits.append(f"Get Free legal assistance, ask up to {self.monthly_questions_limit} legal questions per month")
            if self.free_documents_per_month > 0:
                benefits.append(f"Create and download {self.free_documents_per_month} FREE personalized legal document every month")
            if self.legal_updates:
                benefits.append("Get regular legal updates, news, and tips")
            if self.forum_access:
                benefits.append("Connect with other users and discuss legal topics in relevant forums")
            if self.student_hub_access:
                benefits.append("Connect with fellow students from different universities, share discussions, study notes, past exam papers, and other helpful resources")
        
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
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User Subscription'
        verbose_name_plural = 'User Subscriptions'
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status})"
    
    def is_active(self):
        """Check if subscription is currently active"""
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
        """Get subscription permissions for this user"""
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
        
        return permissions


class Wallet(models.Model):
    """
    User's in-app wallet for transactions
    """
    CURRENCY_CHOICES = [
        ('TZS', 'Tanzanian Shilling'),
    ]
    
    user = models.OneToOneField(PolaUser, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='TZS')
    is_active = models.BooleanField(default=True)
    
    # Earnings tracking (for consultants, uploaders, etc.)
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_withdrawn = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Wallet'
        verbose_name_plural = 'Wallets'
    
    def __str__(self):
        return f"{self.user.email} - {self.balance} {self.currency}"
    
    def has_sufficient_balance(self, amount):
        """Check if wallet has sufficient balance"""
        return self.balance >= amount
    
    def deposit(self, amount, description="Deposit"):
        """Add money to wallet"""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        
        self.balance += Decimal(str(amount))
        self.save()
        
        # Create transaction record
        Transaction.objects.create(
            wallet=self,
            transaction_type='deposit',
            amount=amount,
            status='completed',
            description=description
        )
    
    def withdraw(self, amount, description="Withdrawal"):
        """Withdraw money from wallet"""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        
        if not self.has_sufficient_balance(amount):
            raise ValueError("Insufficient balance")
        
        self.balance -= Decimal(str(amount))
        self.total_withdrawn += Decimal(str(amount))
        self.save()
        
        # Create transaction record
        Transaction.objects.create(
            wallet=self,
            transaction_type='withdrawal',
            amount=amount,
            status='completed',
            description=description
        )
    
    def deduct(self, amount, transaction_type, description):
        """Deduct amount for purchases/subscriptions"""
        if not self.has_sufficient_balance(amount):
            raise ValueError("Insufficient balance")
        
        self.balance -= Decimal(str(amount))
        self.save()
        
        # Create transaction record
        Transaction.objects.create(
            wallet=self,
            transaction_type=transaction_type,
            amount=amount,
            status='completed',
            description=description
        )
    
    def add_earnings(self, amount, transaction_type, description):
        """Add earnings (for consultants, uploaders)"""
        self.balance += Decimal(str(amount))
        self.total_earnings += Decimal(str(amount))
        self.save()
        
        # Create transaction record
        Transaction.objects.create(
            wallet=self,
            transaction_type=transaction_type,
            amount=amount,
            status='completed',
            description=description
        )


class Transaction(models.Model):
    """
    Record of all wallet transactions
    """
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('subscription', 'Subscription Payment'),
        ('consultation_purchase', 'Consultation Voucher Purchase'),
        ('consultation_earning', 'Consultation Earning'),
        ('document_purchase', 'Document Purchase'),
        ('learning_material_purchase', 'Learning Material Purchase'),
        ('learning_material_earning', 'Learning Material Earning'),
        ('refund', 'Refund'),
        ('adjustment', 'Admin Adjustment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    reference = models.CharField(max_length=100, unique=True, blank=True)
    description = models.TextField()
    
    # Payment gateway details
    payment_method = models.CharField(max_length=50, blank=True, null=True, help_text="M-Pesa, Tigo Pesa, Card, etc.")
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    
    # Related objects (optional)
    related_subscription = models.ForeignKey('UserSubscription', on_delete=models.SET_NULL, null=True, blank=True)
    related_voucher = models.ForeignKey('ConsultationVoucher', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        indexes = [
            models.Index(fields=['wallet', '-created_at']),
            models.Index(fields=['reference']),
        ]
    
    def __str__(self):
        return f"{self.wallet.user.email} - {self.transaction_type} - {self.amount} TZS"
    
    def save(self, *args, **kwargs):
        # Generate unique reference if not provided
        if not self.reference:
            import uuid
            self.reference = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)


class ConsultationVoucher(models.Model):
    """
    Consultation vouchers purchased by users
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
    
    def get_pricing_details(self):
        """Return pricing details for this voucher type"""
        pricing = {
            5: {'price': 3000, 'expiry_days': 3},
            10: {'price': 5000, 'expiry_days': 5},
            20: {'price': 9000, 'expiry_days': 7},
        }
        return pricing.get(self.duration_minutes, {})


class ConsultationSession(models.Model):
    """
    Individual consultation sessions
    """
    CONSULTATION_TYPES = [
        ('mobile', 'Mobile Consultation (In-App Call)'),
        ('physical', 'Physical Consultation'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    # Participants
    client = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='client_sessions')
    consultant = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='consultant_sessions')
    
    # Session details
    consultation_type = models.CharField(max_length=20, choices=CONSULTATION_TYPES)
    scheduled_date = models.DateTimeField()
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=0, help_text="Actual duration")
    
    # Payment and revenue split
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    consultant_share = models.DecimalField(max_digits=10, decimal_places=2)
    app_share = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Related voucher (if mobile consultation)
    voucher = models.ForeignKey(ConsultationVoucher, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True, help_text="Session notes or feedback")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_date']
        verbose_name = 'Consultation Session'
        verbose_name_plural = 'Consultation Sessions'
    
    def __str__(self):
        return f"{self.client.email} with {self.consultant.email} - {self.scheduled_date}"
    
    def start_session(self):
        """Mark session as started"""
        self.status = 'ongoing'
        self.start_time = timezone.now()
        self.save()
    
    def end_session(self):
        """Mark session as completed and calculate revenue split"""
        self.status = 'completed'
        self.end_time = timezone.now()
        
        if self.start_time:
            self.duration_minutes = int((self.end_time - self.start_time).total_seconds() / 60)
        
        # Deduct from voucher if mobile consultation
        if self.consultation_type == 'mobile' and self.voucher:
            self.voucher.use_minutes(self.duration_minutes)
        
        # Pay consultant their share
        if hasattr(self.consultant, 'wallet'):
            self.consultant.wallet.add_earnings(
                self.consultant_share,
                'consultation_earning',
                f"Consultation with {self.client.email}"
            )
        
        self.save()
    
    @staticmethod
    def calculate_revenue_split(amount, consultation_type):
        """Calculate revenue split between consultant and app"""
        if consultation_type == 'mobile':
            # 50/50 split for mobile
            consultant_share = amount * Decimal('0.50')
            app_share = amount * Decimal('0.50')
        else:
            # 60/40 split for physical
            consultant_share = amount * Decimal('0.60')
            app_share = amount * Decimal('0.40')
        
        return {
            'consultant_share': consultant_share,
            'app_share': app_share
        }


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


class LearningMaterial(models.Model):
    """
    Learning materials uploaded by students, lecturers, or admins
    """
    UPLOADER_TYPES = [
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
        ('admin', 'Admin'),
    ]
    
    CATEGORY_CHOICES = [
        ('notes', 'Study Notes'),
        ('past_papers', 'Past Exam Papers'),
        ('assignments', 'Assignments'),
        ('tutorials', 'Tutorials'),
        ('other', 'Other'),
    ]
    
    uploader = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='uploaded_materials')
    uploader_type = models.CharField(max_length=20, choices=UPLOADER_TYPES)
    
    # Material details
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    # File
    file = models.FileField(upload_to='learning_materials/')
    file_size = models.BigIntegerField(help_text="File size in bytes")
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Stats
    downloads_count = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    uploader_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    is_approved = models.BooleanField(default=False, help_text="Admin approval required")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Learning Material'
        verbose_name_plural = 'Learning Materials'
    
    def __str__(self):
        return f"{self.title} by {self.uploader.email}"
    
    def get_revenue_split(self):
        """Calculate revenue split based on uploader type"""
        splits = {
            'student': {'uploader': 0.50, 'app': 0.50},  # 50/50
            'lecturer': {'uploader': 0.60, 'app': 0.40},  # 60/40
            'admin': {'uploader': 0.00, 'app': 1.00},  # 100% to app
        }
        return splits.get(self.uploader_type, {'uploader': 0.50, 'app': 0.50})
    
    def record_purchase(self, buyer):
        """Record a purchase and distribute revenue"""
        self.downloads_count += 1
        self.total_revenue += self.price
        
        # Calculate revenue split
        split = self.get_revenue_split()
        uploader_share = self.price * Decimal(str(split['uploader']))
        app_share = self.price * Decimal(str(split['app']))
        
        self.uploader_earnings += uploader_share
        self.save()
        
        # Pay uploader their share
        if uploader_share > 0 and hasattr(self.uploader, 'wallet'):
            self.uploader.wallet.add_earnings(
                uploader_share,
                'learning_material_earning',
                f"Purchase of '{self.title}' by {buyer.email}"
            )
        
        return {
            'uploader_share': uploader_share,
            'app_share': app_share
        }


class LearningMaterialPurchase(models.Model):
    """
    Record of learning material purchases
    """
    buyer = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='learning_purchases')
    material = models.ForeignKey(LearningMaterial, on_delete=models.CASCADE, related_name='purchases')
    
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateTimeField(auto_now_add=True)
    
    # Download tracking
    download_count = models.IntegerField(default=0)
    last_downloaded = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-purchase_date']
        verbose_name = 'Learning Material Purchase'
        verbose_name_plural = 'Learning Material Purchases'
        unique_together = ['buyer', 'material']
    
    def __str__(self):
        return f"{self.buyer.email} - {self.material.title}"
    
    def increment_download(self):
        """Increment download count"""
        self.download_count += 1
        self.last_downloaded = timezone.now()
        self.save()

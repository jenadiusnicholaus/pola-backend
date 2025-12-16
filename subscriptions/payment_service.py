"""
Unified Payment Service
Handles all payment types through a single interface

Payment Categories:
- subscription: Monthly platform access
- call_credit: Consultation credit bundles
- document: Generated legal document downloads  
- material: Study material purchases
"""

import logging
import uuid
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.apps import apps
from django.conf import settings

from .models import (
    PaymentTransaction, SubscriptionPlan, CallCreditBundle,
    GeneratedDocument, UserSubscription, UserCallCredit
)
from .azampay_integration import azampay_client, format_phone_number, detect_mobile_provider

logger = logging.getLogger(__name__)


class PaymentServiceError(Exception):
    """Custom exception for payment service errors"""
    pass


class PaymentService:
    """
    Unified payment processing service
    
    Handles payment initiation and fulfillment for all payment categories
    """
    
    PAYMENT_CATEGORIES = {
        'subscription': {
            'model': SubscriptionPlan,
            'description_field': 'name',
            'amount_field': 'price',
        },
        'call_credit': {
            'model': CallCreditBundle,
            'description_field': 'name',
            'amount_field': 'price',
        },
        'document': {
            'model': GeneratedDocument,
            'description_field': 'title',
            'amount_field': 'price',  # Assuming documents have price field
        },
        'material': {
            'model_path': 'documents.LearningMaterial',
            'description_field': 'title',
            'amount_field': 'price',
        }
    }
    
    def __init__(self):
        self.azampay = azampay_client
    
    def initiate_payment(self, user, payment_category, item_id, payment_method='mobile_money', **kwargs):
        """
        Universal payment initiation
        
        Args:
            user: PolaUser instance
            payment_category: 'subscription', 'call_credit', 'document', 'material'
            item_id: ID of the item being purchased
            payment_method: 'mobile_money' or 'bank'
            **kwargs: phone_number, provider, bank_name, otp, merchant_mobile, etc.
        
        Returns:
            dict: {
                'success': bool,
                'transaction': PaymentTransaction instance,
                'payment_details': dict from AzamPay,
                'message': str
            }
        
        Raises:
            PaymentServiceError: If validation fails or payment initiation fails
        """
        # Validate category
        if payment_category not in self.PAYMENT_CATEGORIES:
            raise PaymentServiceError(f"Invalid payment category: {payment_category}. "
                                     f"Must be one of: {list(self.PAYMENT_CATEGORIES.keys())}")
        
        try:
            # Get item and validate
            item = self._get_item(payment_category, item_id)
            if not item:
                raise PaymentServiceError(f"Item not found: {payment_category} with ID {item_id}")
            
            # Get amount, currency, and description
            amount = self._get_amount(payment_category, item)
            currency = self._get_currency(payment_category, item)
            description = self._generate_description(payment_category, item)
            item_metadata = self._get_item_metadata(payment_category, item)
            
            # Validate amount
            if amount <= 0:
                raise PaymentServiceError(f"Invalid amount: {amount}. Amount must be greater than 0")
            
            # Generate unique payment reference
            payment_reference = self._generate_reference(payment_category)
            
            # Create payment transaction in database
            with transaction.atomic():
                payment_txn = PaymentTransaction.objects.create(
                    user=user,
                    transaction_type=payment_category,
                    amount=amount,
                    currency=currency,
                    payment_method=payment_method,
                    payment_reference=payment_reference,
                    description=description,
                    item_metadata=item_metadata,
                    status='pending'
                )
                
                # Link to specific related object
                self._link_related_object(payment_txn, payment_category, item)
                
                logger.info(f"💳 Payment initiated: {payment_category} for {user.email}, "
                           f"Amount: {amount} {currency}, Ref: {payment_reference}")
                
                # Initiate AzamPay payment
                payment_result = self._initiate_azampay(
                    payment_txn=payment_txn,
                    payment_method=payment_method,
                    **kwargs
                )
                
                if payment_result.get('success'):
                    # Update with gateway reference
                    payment_txn.gateway_reference = payment_result.get('transaction_id', '')
                    payment_txn.save()
                    
                    logger.info(f"✅ AzamPay payment initiated: {payment_result.get('transaction_id')}")
                    
                    # SANDBOX MODE: Fulfill immediately (no webhook callback)
                    # PRODUCTION: Wait for webhook callback
                    if not settings.AZAM_PAY_PRODUCTION:
                        logger.info(f"🧪 SANDBOX MODE: Auto-fulfilling payment immediately")
                        try:
                            # Mark as completed (simulate successful payment)
                            payment_txn.status = 'completed'
                            payment_txn.save()
                            
                            # Fulfill the purchase immediately
                            self.fulfill_payment(payment_txn)
                            logger.info(f"✅ SANDBOX: Payment fulfilled immediately")
                        except Exception as e:
                            logger.error(f"❌ SANDBOX: Auto-fulfillment failed: {str(e)}")
                            # Don't fail the whole payment initiation
                else:
                    # Payment initiation failed
                    payment_txn.mark_failed()
                    logger.error(f"❌ AzamPay payment failed: {payment_result.get('message')}")
                
                return {
                    'success': payment_result.get('success', False),
                    'transaction': payment_txn,
                    'payment_details': payment_result,
                    'message': payment_result.get('message', 'Payment initiated')
                }
        
        except Exception as e:
            logger.error(f"❌ Payment initiation error: {str(e)}")
            raise PaymentServiceError(f"Payment initiation failed: {str(e)}")
    
    def fulfill_payment(self, payment_txn):
        """
        Fulfill a completed payment
        Called by webhook handler after payment confirmation from AzamPay
        
        Args:
            payment_txn: PaymentTransaction instance
        
        Raises:
            PaymentServiceError: If fulfillment fails
        """
        if payment_txn.is_fulfilled:
            logger.warning(f"⚠️ Payment already fulfilled: {payment_txn.payment_reference}")
            return
        
        if payment_txn.status != 'completed':
            raise PaymentServiceError(f"Cannot fulfill payment with status: {payment_txn.status}")
        
        category = payment_txn.transaction_type
        
        try:
            with transaction.atomic():
                # Call category-specific fulfillment
                if category == 'subscription':
                    self._fulfill_subscription(payment_txn)
                elif category == 'call_credit':
                    self._fulfill_call_credit(payment_txn)
                elif category == 'document':
                    self._fulfill_document_download(payment_txn)
                elif category == 'material':
                    self._fulfill_material_purchase(payment_txn)
                else:
                    raise PaymentServiceError(f"Unknown category: {category}")
                
                # Mark as fulfilled
                payment_txn.mark_fulfilled(f"Fulfilled at {timezone.now()}")
                
                logger.info(f"✅ Payment fulfilled: {payment_txn.payment_reference} ({category})")
        
        except Exception as e:
            logger.error(f"❌ Fulfillment error: {str(e)}")
            payment_txn.fulfillment_notes = f"Fulfillment failed: {str(e)}"
            payment_txn.save()
            raise PaymentServiceError(f"Fulfillment failed: {str(e)}")
    
    # =========================================================================
    # PRIVATE HELPER METHODS
    # =========================================================================
    
    def _get_item(self, category, item_id):
        """Get the item being purchased"""
        config = self.PAYMENT_CATEGORIES[category]
        
        if 'model_path' in config:
            # Handle models from other apps
            app_label, model_name = config['model_path'].split('.')
            Model = apps.get_model(app_label, model_name)
        else:
            Model = config['model']
        
        try:
            return Model.objects.get(id=item_id)
        except Model.DoesNotExist:
            return None
    
    def _get_amount(self, category, item):
        """Extract amount from item"""
        config = self.PAYMENT_CATEGORIES[category]
        amount_field = config['amount_field']
        amount = getattr(item, amount_field, 0)
        return Decimal(str(amount))
    
    def _get_currency(self, category, item):
        """Get currency from item (defaults to TZS)"""
        # Most items have a currency field
        currency = getattr(item, 'currency', 'TZS')
        
        # Validate currency code (must be 3 letters)
        if not currency or len(currency) != 3:
            logger.warning(f"Invalid currency '{currency}' for {category}, defaulting to TZS")
            return 'TZS'
        
        return currency.upper()
    
    def _generate_description(self, category, item):
        """Generate human-readable description"""
        config = self.PAYMENT_CATEGORIES[category]
        description_field = config['description_field']
        item_name = getattr(item, description_field, 'Unknown')
        
        category_names = {
            'subscription': 'Subscription',
            'call_credit': 'Call Credit Bundle',
            'document': 'Document',
            'material': 'Study Material'
        }
        
        return f"{category_names[category]}: {item_name}"
    
    def _get_item_metadata(self, category, item):
        """Extract item metadata for storage"""
        metadata = {
            'item_id': item.id,
            'category': category
        }
        
        if category == 'subscription':
            metadata.update({
                'plan_name': item.name,
                'duration_days': item.duration_days,
                'plan_type': item.plan_type
            })
        elif category == 'call_credit':
            metadata.update({
                'bundle_name': item.name,
                'minutes': item.minutes,
                'validity_days': item.validity_days
            })
        elif category == 'document':
            metadata.update({
                'document_title': item.title,
                'document_type': item.document_type
            })
        elif category == 'material':
            metadata.update({
                'material_title': item.title,
                'uploader_id': item.uploader.id if hasattr(item, 'uploader') else None
            })
        
        return metadata
    
    def _generate_reference(self, category):
        """Generate unique payment reference"""
        timestamp = int(timezone.now().timestamp())
        unique_id = uuid.uuid4().hex[:8]
        category_prefix = category.upper()[:3]
        return f"PAY_{category_prefix}_{timestamp}_{unique_id}"
    
    def _link_related_object(self, payment_txn, category, item):
        """Link payment transaction to specific related model"""
        if category == 'subscription':
            payment_txn.related_subscription = None  # Will create after fulfillment
        elif category == 'call_credit':
            payment_txn.related_call_credit = None  # Will create after fulfillment
        elif category == 'document':
            payment_txn.related_document = item
        elif category == 'material':
            payment_txn.related_material = item
        
        payment_txn.save()
    
    def _initiate_azampay(self, payment_txn, payment_method, **kwargs):
        """Initiate payment with AzamPay"""
        if payment_method == 'mobile_money':
            phone_number = kwargs.get('phone_number')
            if not phone_number:
                raise PaymentServiceError("phone_number is required for mobile money payments")
            
            # Format and detect provider
            formatted_phone = format_phone_number(phone_number)
            provider = kwargs.get('provider') or detect_mobile_provider(formatted_phone)
            
            try:
                result = self.azampay.mobile_checkout(
                    account_number=formatted_phone,
                    amount=float(payment_txn.amount),
                    external_id=payment_txn.payment_reference,
                    provider=provider,
                    currency=payment_txn.currency  # Pass currency from payment transaction
                )
                return result
            except Exception as e:
                logger.error(f"AzamPay mobile checkout error: {e}")
                return {
                    'success': False,
                    'message': str(e)
                }
        
        elif payment_method == 'bank':
            # Bank checkout requires OTP
            bank_name = kwargs.get('bank_name')
            otp = kwargs.get('otp')
            merchant_mobile = kwargs.get('merchant_mobile')
            
            if not all([bank_name, otp, merchant_mobile]):
                raise PaymentServiceError("bank_name, otp, and merchant_mobile required for bank payments")
            
            try:
                result = self.azampay.bank_checkout(
                    reference_id=payment_txn.payment_reference,
                    merchant_name="POLA",
                    amount=float(payment_txn.amount),
                    merchant_account_number="0000000000",  # From settings
                    merchant_mobile_number=merchant_mobile,
                    otp=otp,
                    provider=bank_name
                )
                return result
            except Exception as e:
                logger.error(f"AzamPay bank checkout error: {e}")
                return {
                    'success': False,
                    'message': str(e)
                }
        
        else:
            raise PaymentServiceError(f"Unsupported payment method: {payment_method}")
    
    # =========================================================================
    # FULFILLMENT METHODS (Category-specific)
    # =========================================================================
    
    def _fulfill_subscription(self, payment_txn):
        """Activate user subscription"""
        logger.info(f"🔧 Starting subscription fulfillment...")
        logger.info(f"   Payment: {payment_txn.payment_reference}")
        logger.info(f"   User: {payment_txn.user.email}")
        logger.info(f"   Metadata: {payment_txn.item_metadata}")
        
        plan_id = payment_txn.item_metadata.get('item_id')
        if not plan_id:
            raise PaymentServiceError("Missing item_id in payment metadata")
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            logger.info(f"   Plan: {plan.name} ({plan.duration_days} days)")
        except SubscriptionPlan.DoesNotExist:
            raise PaymentServiceError(f"Subscription plan not found: {plan_id}")
        
        # Check for existing active subscription
        existing = UserSubscription.objects.filter(
            user=payment_txn.user,
            status='active'
        ).first()
        
        if existing:
            # UPGRADE/EXTEND existing subscription
            logger.info(f"   Found existing subscription: {existing.plan.name}")
            
            # Determine start date
            if existing.end_date > timezone.now():
                # Active subscription - extend from end date
                start_date = existing.end_date
                logger.info(f"   Extending from current end date: {existing.end_date}")
            else:
                # Expired subscription - start from now
                start_date = timezone.now()
                logger.info(f"   Subscription expired, starting fresh from now")
            
            # UPDATE TO NEW PAID PLAN (important!)
            existing.plan = plan
            existing.end_date = start_date + timedelta(days=plan.duration_days)
            existing.save()
            
            payment_txn.related_subscription = existing
            payment_txn.save()
            
            logger.info(f"✅ UPGRADED subscription to {plan.name} for {payment_txn.user.email}")
            logger.info(f"   Valid until: {existing.end_date}")
        else:
            # Create new subscription
            subscription = UserSubscription.objects.create(
                user=payment_txn.user,
                plan=plan,
                status='active',
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=plan.duration_days),
                auto_renew=False
            )
            
            payment_txn.related_subscription = subscription
            payment_txn.save()
            
            logger.info(f"✅ Created subscription for {payment_txn.user.email}")
    
    def _fulfill_call_credit(self, payment_txn):
        """Add call credits to user account"""
        bundle_id = payment_txn.item_metadata.get('item_id')
        bundle = CallCreditBundle.objects.get(id=bundle_id)
        
        # Create user call credit
        credit = UserCallCredit.objects.create(
            user=payment_txn.user,
            bundle=bundle,
            total_minutes=bundle.minutes,
            remaining_minutes=bundle.minutes,
            expiry_date=timezone.now() + timedelta(days=bundle.validity_days),
            status='active'
        )
        
        payment_txn.related_call_credit = credit
        payment_txn.save()
        
        logger.info(f"✅ Added {bundle.minutes} minutes to {payment_txn.user.email}")
    
    def _fulfill_document_download(self, payment_txn):
        """Grant access to generated document"""
        # Document already linked in related_document
        # Just mark document as purchased (not free)
        document = payment_txn.related_document
        if document:
            document.was_free = False
            document.save()
            
            logger.info(f"✅ Granted document access: {document.title} to {payment_txn.user.email}")
    
    def _fulfill_material_purchase(self, payment_txn):
        """Grant access to study material and distribute earnings"""
        from documents.models import LearningMaterial
        
        material = payment_txn.related_material
        if not material:
            raise PaymentServiceError("Material not found")
        
        # Import MaterialPurchase model
        from .models import MaterialPurchase
        
        # Calculate commission split (assuming 30% platform, 70% uploader)
        platform_commission = payment_txn.amount * Decimal('0.30')
        uploader_earnings = payment_txn.amount * Decimal('0.70')
        
        # Create purchase record
        purchase = MaterialPurchase.objects.create(
            buyer=payment_txn.user,
            material=material,
            amount_paid=payment_txn.amount,
            platform_commission=platform_commission,
            uploader_earnings=uploader_earnings
        )
        
        # TODO: Credit uploader's wallet/earnings
        # This will be implemented when wallet system is ready
        
        logger.info(f"✅ Granted material access: {material.title} to {payment_txn.user.email}")


# Singleton instance for easy import
payment_service = PaymentService()

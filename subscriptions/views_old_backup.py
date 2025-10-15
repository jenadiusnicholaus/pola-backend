from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.db import transaction as db_transaction
from django.db.models import Q, Sum, Count

from .models import (
    SubscriptionPlan,
    UserSubscription,
    # Wallet,  # REMOVED - Replaced by PaymentTransaction
    # Transaction,  # REMOVED - Replaced by PaymentTransaction
    ConsultationVoucher,
    # ConsultationSession,  # REMOVED - Replaced by ConsultationBooking + CallSession
    DocumentType,
    DocumentPurchase,
    LearningMaterial,
    LearningMaterialPurchase,
    # New models - will be integrated in Phase 2
    PaymentTransaction,
    ConsultantRegistrationRequest,
    ConsultantProfile,
    PricingConfiguration,
    ConsultationBooking,
    CallSession,
)
from .serializers import (
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
    # WalletSerializer,  # REMOVED
    # TransactionSerializer,  # REMOVED
    ConsultationVoucherSerializer,
    # ConsultationSessionSerializer,  # REMOVED
    DocumentTypeSerializer,
    DocumentPurchaseSerializer,
    LearningMaterialSerializer,
    LearningMaterialPurchaseSerializer,
    SubscribeSerializer,
    WalletDepositSerializer,
    WalletWithdrawSerializer,
    PurchaseVoucherSerializer,
    BookConsultationSerializer,
    PurchaseDocumentSerializer,
    UploadLearningMaterialSerializer,
    PurchaseLearningMaterialSerializer,
    ConsultantSerializer
)
from authentication.models import PolaUser


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for subscription management
    
    Endpoints:
    - GET /plans/ - List all available plans
    - GET /plans/{id}/ - Get plan details
    - GET /status/ - Check current user's subscription status
    - POST /subscribe/ - Subscribe to a plan
    - POST /cancel/ - Cancel subscription
    - GET /benefits/ - Get subscription benefits
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionPlanSerializer
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get current user's subscription status"""
        try:
            subscription = request.user.subscription
            serializer = UserSubscriptionSerializer(subscription)
            return Response(serializer.data)
        except UserSubscription.DoesNotExist:
            return Response({
                'message': 'No active subscription',
                'has_subscription': False
            })
    
    @action(detail=False, methods=['post'])
    def subscribe(self, request):
        """Subscribe to a plan"""
        serializer = SubscribeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        plan_id = serializer.validated_data['plan_id']
        auto_renew = serializer.validated_data['auto_renew']
        payment_method = serializer.validated_data['payment_method']
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user already has a subscription
        if hasattr(request.user, 'subscription'):
            existing = request.user.subscription
            if existing.is_active():
                return Response({
                    'error': 'You already have an active subscription',
                    'current_plan': plan.name,
                    'expires': existing.end_date
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Process payment
        if payment_method == 'wallet':
            # Deduct from wallet
            try:
                wallet = request.user.wallet
                with db_transaction.atomic():
                    wallet.deduct(
                        plan.price,
                        'subscription',
                        f'Subscription to {plan.name}'
                    )
            except Wallet.DoesNotExist:
                return Response({'error': 'Wallet not found. Please create a wallet first.'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # TODO: Integrate with payment gateway
            return Response({
                'message': 'Payment gateway integration pending',
                'payment_method': payment_method
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
        
        # Create or update subscription
        end_date = timezone.now() + timedelta(days=plan.duration_days)
        
        if hasattr(request.user, 'subscription'):
            subscription = request.user.subscription
            subscription.plan = plan
            subscription.status = 'active'
            subscription.end_date = end_date
            subscription.auto_renew = auto_renew
            subscription.save()
        else:
            subscription = UserSubscription.objects.create(
                user=request.user,
                plan=plan,
                status='active',
                end_date=end_date,
                auto_renew=auto_renew
            )
        
        return Response({
            'message': f'Successfully subscribed to {plan.name}',
            'subscription': UserSubscriptionSerializer(subscription).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def cancel(self, request):
        """Cancel current subscription"""
        try:
            subscription = request.user.subscription
            subscription.cancel_subscription()
            return Response({
                'message': 'Subscription cancelled successfully',
                'subscription': UserSubscriptionSerializer(subscription).data
            })
        except UserSubscription.DoesNotExist:
            return Response({'error': 'No active subscription'}, 
                          status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def benefits(self, request):
        """Get subscription benefits in both languages"""
        language = request.query_params.get('lang', 'en')
        
        # Currency symbols mapping
        currency_symbols = {
            'TZS': 'TSh',
            'USD': '$',
            'EUR': '€',
        }
        
        plans_data = []
        for plan in SubscriptionPlan.objects.filter(is_active=True):
            symbol = currency_symbols.get(plan.currency, plan.currency)
            price_formatted = f"{float(plan.price):,.2f}"
            
            plans_data.append({
                'plan_type': plan.plan_type,
                'name': plan.name if language == 'en' else plan.name_sw,
                'price': float(plan.price),
                'currency': plan.currency,
                'currency_symbol': symbol,
                'price_formatted': f"{symbol} {price_formatted}",
                'duration_days': plan.duration_days,
                'benefits': plan.get_benefits_dict(language=language)
            })
        
        # Get monthly plan for dynamic messaging
        monthly_plan = SubscriptionPlan.objects.filter(
            plan_type='monthly', 
            is_active=True
        ).first()
        
        if monthly_plan:
            monthly_symbol = currency_symbols.get(monthly_plan.currency, monthly_plan.currency)
            monthly_price = float(monthly_plan.price)
            daily_price = monthly_price / 30
            
            daily_value_en = f"For only {daily_price:.0f} {monthly_plan.currency} a day, get legal guidance and assistance anytime"
            daily_value_sw = f"Kwa Shilingi {daily_price:.0f} tu kwa siku, pata mwongozo na msaada wa Kisheria kila wakati"
            
            subscribe_en = f"Subscribe for only {monthly_symbol} {monthly_price:,.0f} per month"
            subscribe_sw = f"Jiunge sasa kwa {monthly_symbol} {monthly_price:,.0f} tu kwa mwezi"
        else:
            # Fallback if no monthly plan
            daily_value_en = "Get legal guidance and assistance anytime"
            daily_value_sw = "Pata mwongozo na msaada wa Kisheria kila wakati"
            subscribe_en = "Subscribe now"
            subscribe_sw = "Jiunge sasa"
        
        return Response({
            'language': language,
            'plans': plans_data,
            'daily_value_message': {
                'en': daily_value_en,
                'sw': daily_value_sw
            },
            'subscribe_button': {
                'en': subscribe_en,
                'sw': subscribe_sw
            }
        })


class WalletViewSet(viewsets.ViewSet):
    """
    ViewSet for wallet management
    
    Endpoints:
    - GET /balance/ - Get wallet balance
    - POST /deposit/ - Deposit money
    - POST /withdraw/ - Withdraw money
    - GET /transactions/ - Get transaction history
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Get wallet balance"""
        try:
            wallet = request.user.wallet
            serializer = WalletSerializer(wallet)
            return Response(serializer.data)
        except Wallet.DoesNotExist:
            # Create wallet if it doesn't exist
            wallet = Wallet.objects.create(user=request.user)
            serializer = WalletSerializer(wallet)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def deposit(self, request):
        """Deposit money into wallet"""
        serializer = WalletDepositSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        amount = serializer.validated_data['amount']
        payment_method = serializer.validated_data['payment_method']
        
        # Get or create wallet
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        
        # TODO: Integrate with payment gateway for actual payment processing
        # For now, we'll simulate successful payment
        if payment_method in ['mpesa', 'tigo_pesa', 'airtel_money']:
            # Simulate payment gateway
            try:
                with db_transaction.atomic():
                    wallet.deposit(amount, f'Deposit via {payment_method}')
                
                return Response({
                    'message': 'Deposit successful',
                    'amount': float(amount),
                    'new_balance': float(wallet.balance),
                    'payment_method': payment_method
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'message': 'Payment gateway integration pending',
                'payment_method': payment_method
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
    
    @action(detail=False, methods=['post'])
    def withdraw(self, request):
        """Withdraw money from wallet"""
        serializer = WalletWithdrawSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        amount = serializer.validated_data['amount']
        withdrawal_method = serializer.validated_data['withdrawal_method']
        account_number = serializer.validated_data['account_number']
        
        try:
            wallet = request.user.wallet
            with db_transaction.atomic():
                wallet.withdraw(amount, f'Withdrawal to {withdrawal_method} - {account_number}')
            
            return Response({
                'message': 'Withdrawal request submitted successfully',
                'amount': float(amount),
                'new_balance': float(wallet.balance),
                'withdrawal_method': withdrawal_method
            })
        except Wallet.DoesNotExist:
            return Response({'error': 'Wallet not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """Get transaction history"""
        try:
            wallet = request.user.wallet
            transactions = wallet.transactions.all()[:50]  # Last 50 transactions
            serializer = TransactionSerializer(transactions, many=True)
            return Response({
                'count': transactions.count(),
                'transactions': serializer.data
            })
        except Wallet.DoesNotExist:
            return Response({'error': 'Wallet not found'}, status=status.HTTP_404_NOT_FOUND)


class ConsultationViewSet(viewsets.ViewSet):
    """
    ViewSet for consultation management
    
    Endpoints:
    - GET /vouchers/ - List user's vouchers
    - POST /vouchers/purchase/ - Purchase consultation voucher
    - POST /book/ - Book a consultation
    - GET /sessions/ - List user's consultation sessions
    - POST /sessions/{id}/start/ - Start a session
    - POST /sessions/{id}/end/ - End a session
    - GET /available/ - List available consultants
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def vouchers(self, request):
        """List user's consultation vouchers"""
        vouchers = ConsultationVoucher.objects.filter(user=request.user)
        serializer = ConsultationVoucherSerializer(vouchers, many=True)
        return Response({
            'count': vouchers.count(),
            'vouchers': serializer.data
        })
    
    @action(detail=False, methods=['post'], url_path='vouchers/purchase')
    def purchase_voucher(self, request):
        """Purchase a consultation voucher"""
        serializer = PurchaseVoucherSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        voucher_type = serializer.validated_data['voucher_type']
        duration_minutes = int(serializer.validated_data['duration_minutes'])
        payment_method = serializer.validated_data['payment_method']
        
        # Get pricing
        pricing = {
            5: {'price': 3000, 'expiry_days': 3},
            10: {'price': 5000, 'expiry_days': 5},
            20: {'price': 9000, 'expiry_days': 7},
        }
        
        if duration_minutes not in pricing:
            return Response({'error': 'Invalid duration'}, status=status.HTTP_400_BAD_REQUEST)
        
        price = pricing[duration_minutes]['price']
        expiry_days = pricing[duration_minutes]['expiry_days']
        
        # Process payment
        if payment_method == 'wallet':
            try:
                wallet = request.user.wallet
                with db_transaction.atomic():
                    # Create voucher
                    voucher = ConsultationVoucher.objects.create(
                        user=request.user,
                        voucher_type=voucher_type,
                        duration_minutes=duration_minutes,
                        remaining_minutes=duration_minutes,
                        amount_paid=price,
                        expiry_date=timezone.now() + timedelta(days=expiry_days)
                    )
                    
                    # Deduct from wallet
                    wallet.deduct(
                        price,
                        'consultation_purchase',
                        f'Purchase {duration_minutes} minute {voucher_type} consultation voucher'
                    )
                
                return Response({
                    'message': 'Voucher purchased successfully',
                    'voucher': ConsultationVoucherSerializer(voucher).data
                }, status=status.HTTP_201_CREATED)
            except Wallet.DoesNotExist:
                return Response({'error': 'Wallet not found'}, status=status.HTTP_404_NOT_FOUND)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'message': 'Payment gateway integration pending',
                'payment_method': payment_method
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
    
    @action(detail=False, methods=['post'])
    def book(self, request):
        """Book a consultation session"""
        serializer = BookConsultationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        consultant_id = serializer.validated_data['consultant_id']
        consultation_type = serializer.validated_data['consultation_type']
        scheduled_date = serializer.validated_data['scheduled_date']
        voucher_id = serializer.validated_data.get('voucher_id')
        notes = serializer.validated_data.get('notes', '')
        
        # Get consultant
        try:
            consultant = PolaUser.objects.get(id=consultant_id)
        except PolaUser.DoesNotExist:
            return Response({'error': 'Consultant not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Determine pricing based on consultant role and type
        if consultation_type == 'mobile':
            # For mobile, use voucher
            if not voucher_id:
                return Response({'error': 'Voucher required for mobile consultations'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            try:
                voucher = ConsultationVoucher.objects.get(id=voucher_id, user=request.user)
                if not voucher.is_active():
                    return Response({'error': 'Voucher is not active or has expired'}, 
                                  status=status.HTTP_400_BAD_REQUEST)
            except ConsultationVoucher.DoesNotExist:
                return Response({'error': 'Voucher not found'}, status=status.HTTP_404_NOT_FOUND)
            
            total_amount = voucher.amount_paid
        else:
            # Physical consultation pricing
            role_pricing = {
                'advocate': 60000,
                'lawyer': 35000,
                'paralegal': 25000,
            }
            consultant_role = consultant.user_role.role_name if consultant.user_role else 'paralegal'
            total_amount = role_pricing.get(consultant_role, 25000)
        
        # Calculate revenue split
        splits = ConsultationSession.calculate_revenue_split(
            Decimal(str(total_amount)),
            consultation_type
        )
        
        # Create session
        session = ConsultationSession.objects.create(
            client=request.user,
            consultant=consultant,
            consultation_type=consultation_type,
            scheduled_date=scheduled_date,
            total_amount=total_amount,
            consultant_share=splits['consultant_share'],
            app_share=splits['app_share'],
            voucher=voucher if consultation_type == 'mobile' else None,
            notes=notes
        )
        
        return Response({
            'message': 'Consultation booked successfully',
            'session': ConsultationSessionSerializer(session).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def sessions(self, request):
        """List user's consultation sessions"""
        # Sessions where user is either client or consultant
        sessions = ConsultationSession.objects.filter(
            Q(client=request.user) | Q(consultant=request.user)
        ).order_by('-scheduled_date')
        
        serializer = ConsultationSessionSerializer(sessions, many=True)
        return Response({
            'count': sessions.count(),
            'sessions': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start a consultation session"""
        try:
            session = ConsultationSession.objects.get(id=pk)
            
            # Only consultant can start
            if session.consultant != request.user:
                return Response({'error': 'Only consultant can start the session'}, 
                              status=status.HTTP_403_FORBIDDEN)
            
            session.start_session()
            return Response({
                'message': 'Session started',
                'session': ConsultationSessionSerializer(session).data
            })
        except ConsultationSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """End a consultation session"""
        try:
            session = ConsultationSession.objects.get(id=pk)
            
            # Only consultant can end
            if session.consultant != request.user:
                return Response({'error': 'Only consultant can end the session'}, 
                              status=status.HTTP_403_FORBIDDEN)
            
            session.end_session()
            return Response({
                'message': 'Session completed and payment processed',
                'session': ConsultationSessionSerializer(session).data
            })
        except ConsultationSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """List available consultants"""
        # Get users with consultant roles (advocate, lawyer, paralegal)
        consultants = PolaUser.objects.filter(
            user_role__role_name__in=['advocate', 'lawyer', 'paralegal']
        ).filter(is_active=True)
        
        serializer = ConsultantSerializer(consultants, many=True)
        return Response({
            'count': consultants.count(),
            'consultants': serializer.data
        })


class DocumentViewSet(viewsets.ViewSet):
    """
    ViewSet for document management
    
    Endpoints:
    - GET /types/ - List document types
    - POST /purchase/ - Purchase a document
    - GET /purchased/ - List purchased documents
    - POST /download/{id}/ - Download a document
    - GET /free-monthly/ - Check free monthly document eligibility
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def types(self, request):
        """List available document types"""
        doc_types = DocumentType.objects.filter(is_active=True)
        serializer = DocumentTypeSerializer(doc_types, many=True)
        return Response({
            'count': doc_types.count(),
            'document_types': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def purchase(self, request):
        """Purchase a document"""
        serializer = PurchaseDocumentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        document_type_id = serializer.validated_data['document_type_id']
        document_data = serializer.validated_data['document_data']
        use_free_monthly = serializer.validated_data['use_free_monthly']
        payment_method = serializer.validated_data['payment_method']
        
        try:
            doc_type = DocumentType.objects.get(id=document_type_id, is_active=True)
        except DocumentType.DoesNotExist:
            return Response({'error': 'Document type not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user can use free monthly document
        was_free = False
        if use_free_monthly:
            try:
                subscription = request.user.subscription
                if subscription.can_generate_free_document() and doc_type.category == 'standard':
                    was_free = True
                    subscription.increment_documents_count()
                else:
                    return Response({
                        'error': 'Cannot use free monthly document. Either limit reached or document is not standard.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except UserSubscription.DoesNotExist:
                return Response({'error': 'Active subscription required'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        
        amount_paid = 0 if was_free else doc_type.price
        
        # Process payment if not free
        if not was_free and payment_method == 'wallet':
            try:
                wallet = request.user.wallet
                with db_transaction.atomic():
                    wallet.deduct(
                        amount_paid,
                        'document_purchase',
                        f'Purchase of {doc_type.name}'
                    )
            except Wallet.DoesNotExist:
                return Response({'error': 'Wallet not found'}, status=status.HTTP_404_NOT_FOUND)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create purchase record
        purchase = DocumentPurchase.objects.create(
            user=request.user,
            document_type=doc_type,
            amount_paid=amount_paid,
            was_free=was_free,
            document_data=document_data
        )
        
        # Increment download count for document type
        doc_type.increment_downloads()
        
        return Response({
            'message': 'Document purchased successfully' if not was_free else 'Free document generated',
            'purchase': DocumentPurchaseSerializer(purchase).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def purchased(self, request):
        """List user's purchased documents"""
        purchases = DocumentPurchase.objects.filter(user=request.user)
        serializer = DocumentPurchaseSerializer(purchases, many=True)
        return Response({
            'count': purchases.count(),
            'documents': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        """Download a purchased document"""
        try:
            purchase = DocumentPurchase.objects.get(id=pk, user=request.user)
            purchase.increment_download()
            
            return Response({
                'message': 'Document download tracked',
                'download_count': purchase.download_count,
                'document': DocumentPurchaseSerializer(purchase).data
            })
        except DocumentPurchase.DoesNotExist:
            return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], url_path='free-monthly')
    def free_monthly(self, request):
        """Check if user can generate free monthly document"""
        try:
            subscription = request.user.subscription
            can_generate = subscription.can_generate_free_document()
            
            return Response({
                'can_generate_free': can_generate,
                'documents_used_this_month': subscription.documents_generated_this_month,
                'monthly_limit': subscription.plan.free_documents_per_month
            })
        except UserSubscription.DoesNotExist:
            return Response({
                'error': 'No active subscription',
                'can_generate_free': False
            }, status=status.HTTP_404_NOT_FOUND)


class LearningMaterialViewSet(viewsets.ViewSet):
    """
    ViewSet for learning material management
    
    Endpoints:
    - GET /materials/ - Browse learning materials
    - POST /upload/ - Upload learning material
    - GET /my-uploads/ - User's uploaded materials
    - POST /purchase/{id}/ - Purchase a material
    - GET /my-purchases/ - User's purchased materials
    - GET /earnings/ - Uploader's earnings
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def materials(self, request):
        """Browse approved learning materials"""
        materials = LearningMaterial.objects.filter(is_approved=True, is_active=True)
        
        # Filters
        category = request.query_params.get('category')
        uploader_type = request.query_params.get('uploader_type')
        
        if category:
            materials = materials.filter(category=category)
        if uploader_type:
            materials = materials.filter(uploader_type=uploader_type)
        
        serializer = LearningMaterialSerializer(materials, many=True)
        return Response({
            'count': materials.count(),
            'materials': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload learning material"""
        serializer = UploadLearningMaterialSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Determine uploader type based on user role
        user_role = request.user.user_role.role_name if request.user.user_role else 'citizen'
        
        if user_role == 'law_student':
            uploader_type = 'student'
            suggested_price = 1500
        elif user_role in ['advocate', 'lawyer']:
            uploader_type = 'lecturer'
            suggested_price = 5000
        elif request.user.is_staff:
            uploader_type = 'admin'
            suggested_price = 3000
        else:
            uploader_type = 'student'
            suggested_price = 1500
        
        uploaded_file = serializer.validated_data['file']
        file_size = uploaded_file.size
        
        material = LearningMaterial.objects.create(
            uploader=request.user,
            uploader_type=uploader_type,
            title=serializer.validated_data['title'],
            description=serializer.validated_data['description'],
            category=serializer.validated_data['category'],
            file=uploaded_file,
            file_size=file_size,
            price=serializer.validated_data['price'],
            is_approved=request.user.is_staff  # Auto-approve admin uploads
        )
        
        return Response({
            'message': 'Material uploaded successfully. Awaiting admin approval.' if not material.is_approved else 'Material uploaded and published.',
            'material': LearningMaterialSerializer(material).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], url_path='my-uploads')
    def my_uploads(self, request):
        """List user's uploaded materials"""
        materials = LearningMaterial.objects.filter(uploader=request.user)
        serializer = LearningMaterialSerializer(materials, many=True)
        return Response({
            'count': materials.count(),
            'materials': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def purchase(self, request, pk=None):
        """Purchase a learning material"""
        serializer = PurchaseLearningMaterialSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        payment_method = serializer.validated_data['payment_method']
        
        try:
            material = LearningMaterial.objects.get(id=pk, is_approved=True, is_active=True)
        except LearningMaterial.DoesNotExist:
            return Response({'error': 'Material not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if already purchased
        if LearningMaterialPurchase.objects.filter(buyer=request.user, material=material).exists():
            return Response({'error': 'You have already purchased this material'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Process payment
        if payment_method == 'wallet':
            try:
                wallet = request.user.wallet
                with db_transaction.atomic():
                    # Create purchase
                    purchase = LearningMaterialPurchase.objects.create(
                        buyer=request.user,
                        material=material,
                        amount_paid=material.price
                    )
                    
                    # Deduct from buyer's wallet
                    wallet.deduct(
                        material.price,
                        'learning_material_purchase',
                        f'Purchase of learning material: {material.title}'
                    )
                    
                    # Record purchase and distribute revenue
                    material.record_purchase(request.user)
                
                return Response({
                    'message': 'Material purchased successfully',
                    'purchase': LearningMaterialPurchaseSerializer(purchase).data
                }, status=status.HTTP_201_CREATED)
            except Wallet.DoesNotExist:
                return Response({'error': 'Wallet not found'}, status=status.HTTP_404_NOT_FOUND)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'message': 'Payment gateway integration pending',
                'payment_method': payment_method
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
    
    @action(detail=False, methods=['get'], url_path='my-purchases')
    def my_purchases(self, request):
        """List user's purchased materials"""
        purchases = LearningMaterialPurchase.objects.filter(buyer=request.user)
        serializer = LearningMaterialPurchaseSerializer(purchases, many=True)
        return Response({
            'count': purchases.count(),
            'purchases': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def earnings(self, request):
        """Get uploader's earnings summary"""
        materials = LearningMaterial.objects.filter(uploader=request.user)
        
        total_revenue = materials.aggregate(Sum('total_revenue'))['total_revenue__sum'] or 0
        total_earnings = materials.aggregate(Sum('uploader_earnings'))['uploader_earnings__sum'] or 0
        total_downloads = materials.aggregate(Sum('downloads_count'))['downloads_count__sum'] or 0
        
        return Response({
            'total_materials': materials.count(),
            'total_downloads': total_downloads,
            'total_revenue': float(total_revenue),
            'your_earnings': float(total_earnings),
            'wallet_balance': float(request.user.wallet.balance) if hasattr(request.user, 'wallet') else 0
        })

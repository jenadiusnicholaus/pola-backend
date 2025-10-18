"""
Seed subscription data only (no user creation)
Usage: python manage.py seed_subscriptions --clear
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum
from decimal import Decimal
from datetime import timedelta
import random

from subscriptions.models import (
    SubscriptionPlan, UserSubscription,
    CallCreditBundle, UserCallCredit,
    ConsultationBooking, ConsultantEarnings,
    LearningMaterial, UploaderEarnings,
    PaymentTransaction, Disbursement
)
from authentication.models import PolaUser


class Command(BaseCommand):
    help = 'Seeds subscription-related data only (uses existing users)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing subscription data before seeding',
        )

    def handle(self, *args, **options):
        # Check if users exist
        if not PolaUser.objects.exists():
            self.stdout.write(self.style.ERROR('❌ No users found! Please create users first.'))
            return

        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing subscription data...'))
            self.clear_data()

        self.stdout.write(self.style.SUCCESS('Starting subscription data seeding...'))
        
        users = list(PolaUser.objects.all())
        self.stdout.write(f'Found {len(users)} existing users')
        
        with transaction.atomic():
            # 1. Create Subscription Plans
            self.stdout.write('Creating subscription plans...')
            plans = self.create_subscription_plans()
            
            # 2. Create User Subscriptions
            self.stdout.write('Creating user subscriptions...')
            subscriptions = self.create_user_subscriptions(users, plans)
            
            # 3. Create Call Credit Bundles
            self.stdout.write('Creating call credit bundles...')
            bundles = self.create_call_credit_bundles()
            
            # 4. Create User Call Credits
            self.stdout.write('Creating user call credits...')
            credits = self.create_user_call_credits(users, bundles)
            
            # 5. Create Learning Materials
            self.stdout.write('Creating learning materials...')
            materials = self.create_learning_materials(users)
            
            # 6. Create Consultation Bookings
            self.stdout.write('Creating consultation bookings...')
            bookings = self.create_consultation_bookings(users)
            
            # 7. Create Payment Transactions
            self.stdout.write('Creating payment transactions...')
            self.create_payment_transactions(users, subscriptions, bookings)
            
            # 8. Create Consultant Earnings
            self.stdout.write('Creating consultant earnings...')
            self.create_consultant_earnings(bookings)
            
            # 9. Create Uploader Earnings
            self.stdout.write('Creating uploader earnings...')
            self.create_uploader_earnings(materials)
            
            # 10. Create Disbursements
            self.stdout.write('Creating disbursements...')
            self.create_disbursements(users)
        
        self.stdout.write(self.style.SUCCESS('\n✅ Subscription data seeding completed!'))
        self.print_summary()

    def clear_data(self):
        """Clear subscription data only"""
        Disbursement.objects.all().delete()
        UploaderEarnings.objects.all().delete()
        ConsultantEarnings.objects.all().delete()
        PaymentTransaction.objects.all().delete()
        ConsultationBooking.objects.all().delete()
        LearningMaterial.objects.all().delete()
        UserCallCredit.objects.all().delete()
        CallCreditBundle.objects.all().delete()
        UserSubscription.objects.all().delete()
        SubscriptionPlan.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✓ Subscription data cleared!'))

    def create_subscription_plans(self):
        """Create subscription plans"""
        plans_data = [
            {
                'plan_type': 'free_trial',
                'name': 'Free Trial',
                'name_sw': 'Jaribu Bure',
                'description': '24 hours (1 day) free access for new users. One device only sign in. Have Premium features which they cannot fully access during the free trial.',
                'description_sw': 'Ufikiaji wa bure wa masaa 24 (siku 1) kwa watumiaji wapya. Ingia kwenye kifaa kimoja tu. Una vipengele vya Premium ambavyo hawawezi kufikia kikamili wakati wa jaribio la bure.',
                'price': Decimal('0.00'),
                'duration_days': 1,
                'is_active': True,
                'full_legal_library_access': True,  # Limited preview access
                'monthly_questions_limit': 2,  # Very limited
                'free_documents_per_month': 0,  # No free documents
                'legal_updates': False,
                'forum_access': True,  # Can view but limited participation
                'student_hub_access': True  # Can view but limited
            },
            {
                'plan_type': 'monthly',
                'name': 'Monthly Subscription',
                'name_sw': 'Usajili wa Kila Mwezi',
                'description': 'For only 100 shillings a day, get legal guidance and assistance anytime',
                'description_sw': 'Kwa Shilingi 100 tu kwa siku, pata mwongozo na msaada wa Kisheria kila wakati',
                'price': Decimal('3000.00'),
                'duration_days': 30,
                'is_active': True,
                'full_legal_library_access': True,
                'monthly_questions_limit': 10,
                'free_documents_per_month': 1,
                'legal_updates': True,
                'forum_access': True,
                'student_hub_access': True
            }
        ]
        
        plans = []
        for plan_data in plans_data:
            plan, created = SubscriptionPlan.objects.update_or_create(
                plan_type=plan_data['plan_type'],
                defaults=plan_data
            )
            plans.append(plan)
            status = '✓ Created' if created else '↻ Updated'
            self.stdout.write(f'  {status}: {plan.name}')
        
        return plans

    def create_user_subscriptions(self, users, plans):
        """Create user subscriptions (one per user due to unique constraint)"""
        subscriptions = []
        now = timezone.now()
        
        # Create subscriptions for up to 50 random users (one subscription per user)
        num_subscriptions = min(50, len(users))
        selected_users = random.sample(users, num_subscriptions)
        
        for user in selected_users:
            plan = random.choice(plans)
            
            start_date = now - timedelta(days=random.randint(0, 60))
            end_date = start_date + timedelta(days=plan.duration_days)
            
            # Determine status
            if end_date > now:
                status = 'active'
            elif random.random() > 0.7:
                status = 'cancelled'
            else:
                status = 'expired'
            
            subscription, created = UserSubscription.objects.update_or_create(
                user=user,
                defaults={
                    'plan': plan,
                    'start_date': start_date,
                    'end_date': end_date,
                    'status': status,
                    'auto_renew': random.choice([True, False])
                }
            )
            subscriptions.append(subscription)
            
        self.stdout.write(f'  ✓ Created/Updated {len(subscriptions)} subscriptions')
        return subscriptions

    def create_call_credit_bundles(self):
        """Create call credit bundles"""
        bundles_data = [
            {'name': '30 Minutes', 'minutes': 30, 'price': Decimal('10000.00'), 'validity_days': 30, 'is_active': True},
            {'name': '60 Minutes', 'minutes': 60, 'price': Decimal('18000.00'), 'validity_days': 30, 'is_active': True},
            {'name': '120 Minutes', 'minutes': 120, 'price': Decimal('32000.00'), 'validity_days': 60, 'is_active': True},
        ]
        
        bundles = []
        for bundle_data in bundles_data:
            bundle, created = CallCreditBundle.objects.update_or_create(
                name=bundle_data['name'],
                defaults=bundle_data
            )
            bundles.append(bundle)
            status = '✓ Created' if created else '↻ Updated'
            self.stdout.write(f'  {status}: {bundle.name}')
        
        return bundles

    def create_user_call_credits(self, users, bundles):
        """Create user call credits"""
        credits = []
        now = timezone.now()
        
        # Create 30 call credits
        for i in range(30):
            user = random.choice(users)
            bundle = random.choice(bundles)
            
            purchase_date = now - timedelta(days=random.randint(0, 45))
            expiry_date = purchase_date + timedelta(days=bundle.validity_days)
            
            total_minutes = bundle.minutes
            remaining_minutes = random.randint(0, total_minutes)
            
            status = 'active' if expiry_date > now and remaining_minutes > 0 else 'expired'
            
            credit = UserCallCredit.objects.create(
                user=user,
                bundle=bundle,
                total_minutes=total_minutes,
                remaining_minutes=remaining_minutes,
                purchase_date=purchase_date,
                expiry_date=expiry_date,
                status=status
            )
            credits.append(credit)
        
        self.stdout.write(f'  ✓ Created {len(credits)} call credits')
        return credits

    def create_learning_materials(self, users):
        """Create learning materials"""
        materials = []
        now = timezone.now()
        
        categories = ['notes', 'past_papers', 'assignments', 'tutorials', 'other']
        uploader_types = ['student', 'lecturer', 'admin']
        
        # Create 25 materials
        for i in range(1, 26):
            uploader = random.choice(users)
            uploader_type = random.choice(uploader_types)
            
            # Generate realistic file size (between 100KB and 10MB)
            file_size = random.randint(100 * 1024, 10 * 1024 * 1024)
            
            material = LearningMaterial.objects.create(
                title=f'Legal Study Material {i}',
                description=f'Comprehensive legal education material #{i}',
                uploader=uploader,
                uploader_type=uploader_type,
                category=random.choice(categories),
                file=f'learning_materials/sample_material_{i}.pdf',  # Placeholder path
                file_size=file_size,
                price=Decimal(random.randint(5, 20)) * 1000,
                is_active=True,
                is_approved=random.choice([True, True, False]),  # 66% approved
                created_at=now - timedelta(days=random.randint(0, 90))
            )
            materials.append(material)
        
        self.stdout.write(f'  ✓ Created {len(materials)} learning materials')
        return materials

    def create_consultation_bookings(self, users):
        """Create consultation bookings"""
        bookings = []
        now = timezone.now()
        
        statuses = ['pending', 'confirmed', 'completed', 'cancelled']
        
        # Create 40 bookings
        for i in range(40):
            client = random.choice(users)
            consultant = random.choice(users)
            
            # Skip if same user
            if client == consultant:
                continue
            
            scheduled_date = now - timedelta(days=random.randint(-10, 30))
            status = random.choice(statuses)
            
            total_amount = Decimal('100000.00')
            platform_commission = total_amount * Decimal('0.4')
            consultant_earnings_amount = total_amount - platform_commission
            
            booking = ConsultationBooking.objects.create(
                client=client,
                consultant=consultant,
                booking_type=random.choice(['mobile', 'physical']),
                status=status,
                scheduled_date=scheduled_date,
                scheduled_duration_minutes=random.choice([30, 60, 90]),
                total_amount=total_amount,
                platform_commission=platform_commission,
                consultant_earnings=consultant_earnings_amount,
                meeting_location='Office' if random.random() > 0.5 else 'Online',
                client_notes=f'Consultation request {i}',
                created_at=scheduled_date - timedelta(days=random.randint(1, 7))
            )
            
            if status == 'completed':
                booking.actual_start_time = scheduled_date
                booking.actual_end_time = scheduled_date + timedelta(hours=1)
                booking.actual_duration_minutes = 60
                booking.save()
            
            bookings.append(booking)
        
        self.stdout.write(f'  ✓ Created {len(bookings)} consultation bookings')
        return bookings

    def create_payment_transactions(self, users, subscriptions, bookings):
        """Create payment transactions"""
        transactions = []
        now = timezone.now()
        
        transaction_types = ['subscription', 'call_credit', 'consultation', 'material', 'document']
        
        # Create 100 transactions
        for i in range(100):
            user = random.choice(users)
            trans_type = random.choice(transaction_types)
            
            amount = Decimal(random.randint(30, 1000)) * 100
            status = random.choices(
                ['completed', 'pending', 'failed'],
                weights=[0.8, 0.1, 0.1]
            )[0]
            
            # Link to subscription or booking if applicable
            related_sub = None
            related_booking = None
            
            if trans_type == 'subscription' and subscriptions:
                related_sub = random.choice(subscriptions)
            elif trans_type == 'consultation' and bookings:
                related_booking = random.choice(bookings)
            
            transaction = PaymentTransaction.objects.create(
                user=user,
                transaction_type=trans_type,
                amount=amount,
                payment_method=random.choice(['azampay', 'mpesa', 'tigopesa']),
                payment_reference=f'PAY{int(now.timestamp())}{i:04d}',
                status=status,
                related_subscription=related_sub,
                related_booking=related_booking,
                created_at=now - timedelta(days=random.randint(0, 60))
            )
            transactions.append(transaction)
        
        self.stdout.write(f'  ✓ Created {len(transactions)} payment transactions')
        return transactions

    def create_consultant_earnings(self, bookings):
        """Create consultant earnings"""
        earnings = []
        
        completed_bookings = [b for b in bookings if b.status == 'completed']
        
        for booking in completed_bookings[:20]:  # First 20 completed bookings
            earning = ConsultantEarnings.objects.create(
                consultant=booking.consultant,
                booking=booking,
                service_type=f'{booking.booking_type}_consultation',
                gross_amount=booking.total_amount,
                platform_commission=booking.platform_commission,
                net_earnings=booking.consultant_earnings,
                paid_out=random.choice([True, False])
            )
            earnings.append(earning)
        
        self.stdout.write(f'  ✓ Created {len(earnings)} consultant earnings')
        return earnings

    def create_uploader_earnings(self, materials):
        """Create uploader earnings"""
        earnings = []
        
        approved_materials = [m for m in materials if m.is_approved]
        
        for material in approved_materials[:15]:  # First 15 approved materials
            gross = material.price * Decimal(random.randint(1, 10))
            commission = gross * Decimal('0.5')
            net = gross - commission
            
            earning = UploaderEarnings.objects.create(
                uploader=material.uploader,
                material=material,
                service_type='material_download',
                gross_amount=gross,
                platform_commission=commission,
                net_earnings=net,
                paid_out=random.choice([True, False])
            )
            earnings.append(earning)
        
        self.stdout.write(f'  ✓ Created {len(earnings)} uploader earnings')
        return earnings

    def create_disbursements(self, users):
        """Create disbursements"""
        disbursements = []
        now = timezone.now()
        
        admin = PolaUser.objects.filter(is_staff=True).first()
        if not admin:
            self.stdout.write(self.style.WARNING('  ⚠ No admin user found, skipping disbursements'))
            return disbursements
        
        statuses = ['pending', 'processing', 'completed', 'failed']
        
        # Create 15 disbursements
        for i in range(15):
            recipient = random.choice(users)
            
            status = random.choice(statuses)
            amount = Decimal(random.randint(50, 500)) * 1000
            
            disbursement = Disbursement.objects.create(
                recipient=recipient,
                recipient_phone=f'+25571234{i:04d}',
                disbursement_type=random.choice(['consultant', 'uploader']),
                amount=amount,
                payment_method='tigo_pesa',
                status=status,
                initiated_by=admin,
                initiated_at=now - timedelta(days=random.randint(0, 30))
            )
            
            if status == 'completed':
                disbursement.completed_at = disbursement.initiated_at + timedelta(hours=random.randint(1, 48))
                disbursement.save()
            
            disbursements.append(disbursement)
        
        self.stdout.write(f'  ✓ Created {len(disbursements)} disbursements')
        return disbursements

    def print_summary(self):
        """Print summary of created data"""
        self.stdout.write(self.style.SUCCESS('\n📊 SUBSCRIPTION DATA SUMMARY'))
        self.stdout.write('━' * 40)
        self.stdout.write(f'Subscription Plans:      {SubscriptionPlan.objects.count():>3}')
        self.stdout.write(f'User Subscriptions:      {UserSubscription.objects.count():>3}')
        self.stdout.write(f'Call Credit Bundles:     {CallCreditBundle.objects.count():>3}')
        self.stdout.write(f'User Call Credits:       {UserCallCredit.objects.count():>3}')
        self.stdout.write(f'Learning Materials:      {LearningMaterial.objects.count():>3}')
        self.stdout.write(f'Consultation Bookings:   {ConsultationBooking.objects.count():>3}')
        self.stdout.write(f'Payment Transactions:    {PaymentTransaction.objects.count():>3}')
        self.stdout.write(f'Consultant Earnings:     {ConsultantEarnings.objects.count():>3}')
        self.stdout.write(f'Uploader Earnings:       {UploaderEarnings.objects.count():>3}')
        self.stdout.write(f'Disbursements:           {Disbursement.objects.count():>3}')
        self.stdout.write('━' * 40)
        
        # Show active subscriptions
        active_subs = UserSubscription.objects.filter(status='active').count()
        self.stdout.write(f'\n✓ Active Subscriptions:  {active_subs}')
        
        # Show revenue stats
        total_revenue = PaymentTransaction.objects.filter(
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        self.stdout.write(f'✓ Total Revenue:         TZS {total_revenue:,.2f}')
        
        self.stdout.write('\n')

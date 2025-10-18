"""
Seed test data for all tables
Usage: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
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
from authentication.models import PolaUser, UserRole, Contact


class Command(BaseCommand):
    help = 'Seeds the database with test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            self.clear_data()

        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))
        
        with transaction.atomic():
            # 1. Create User Roles
            self.stdout.write('Creating user roles...')
            roles = self.create_user_roles()
            
            # 2. Create Users
            self.stdout.write('Creating users...')
            users = self.create_users(roles)
            
            # 3. Create Subscription Plans
            self.stdout.write('Creating subscription plans...')
            plans = self.create_subscription_plans()
            
            # 4. Create User Subscriptions
            self.stdout.write('Creating user subscriptions...')
            subscriptions = self.create_user_subscriptions(users, plans)
            
            # 5. Create Call Credit Bundles
            self.stdout.write('Creating call credit bundles...')
            bundles = self.create_call_credit_bundles()
            
            # 6. Create User Call Credits
            self.stdout.write('Creating user call credits...')
            credits = self.create_user_call_credits(users, bundles)
            
            # 7. Create Learning Materials
            self.stdout.write('Creating learning materials...')
            materials = self.create_learning_materials(users)
            
            # 8. Create Consultation Bookings
            self.stdout.write('Creating consultation bookings...')
            bookings = self.create_consultation_bookings(users)
            
            # 9. Create Payment Transactions
            self.stdout.write('Creating payment transactions...')
            self.create_payment_transactions(users, subscriptions, bookings)
            
            # 10. Create Consultant Earnings
            self.stdout.write('Creating consultant earnings...')
            self.create_consultant_earnings(users, bookings)
            
            # 11. Create Uploader Earnings
            self.stdout.write('Creating uploader earnings...')
            self.create_uploader_earnings(users, materials)
            
            # 12. Create Disbursements
            self.stdout.write('Creating disbursements...')
            self.create_disbursements(users)
        
        self.stdout.write(self.style.SUCCESS('✅ Data seeding completed successfully!'))
        self.print_summary()

    def clear_data(self):
        """Clear existing data"""
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
        Contact.objects.all().delete()
        PolaUser.objects.filter(is_superuser=False).delete()  # Keep superusers
        self.stdout.write(self.style.SUCCESS('Data cleared!'))

    def create_user_roles(self):
        """Create user roles"""
        roles_data = [
            'citizen', 'advocate', 'lawyer', 
            'law_student', 'law_firm', 'paralegal'
        ]
        
        roles = {}
        for role_name in roles_data:
            role, created = UserRole.objects.get_or_create(role_name=role_name)
            roles[role_name] = role
            if created:
                self.stdout.write(f'  Created role: {role_name}')
        
        return roles

    def create_users(self, roles):
        """Create test users"""
        users = {}
        now = timezone.now()
        
        self.stdout.write('  Creating citizens...')
        # Create citizens
        for i in range(1, 21):
            email = f'citizen{i}@example.com'
            
            # Check if user already exists
            if PolaUser.objects.filter(email=email).exists():
                user = PolaUser.objects.get(email=email)
                users.setdefault('citizen', []).append(user)
                continue
            
            user = PolaUser.objects.create(
                email=email,
                first_name=f'Citizen{i}',
                last_name=f'User',
                user_role=roles['citizen'],
                is_active=True,
                date_joined=now - timedelta(days=random.randint(1, 365))
            )
            user.set_password('password123')
            user.save()
            
            Contact.objects.create(
                user=user,
                phone_number=f'+25571234{i:04d}',
                phone_is_verified=True
            )
            users.setdefault('citizen', []).append(user)
            
            if i % 5 == 0:
                self.stdout.write(f'    Created {i} citizens...')
        
        self.stdout.write('  Creating advocates...')
        # Create advocates
        for i in range(1, 6):
            email = f'advocate{i}@example.com'
            
            if PolaUser.objects.filter(email=email).exists():
                user = PolaUser.objects.get(email=email)
                users.setdefault('advocate', []).append(user)
                continue
            
            user = PolaUser.objects.create(
                email=email,
                first_name=f'Advocate{i}',
                last_name=f'Legal',
                user_role=roles['advocate'],
                is_active=True,
                date_joined=now - timedelta(days=random.randint(1, 365))
            )
            user.set_password('password123')
            user.save()
            
            Contact.objects.create(
                user=user,
                phone_number=f'+25571234{100+i:04d}',
                phone_is_verified=True
            )
            users.setdefault('advocate', []).append(user)
        
        self.stdout.write('  Creating lawyers...')
        # Create lawyers
        for i in range(1, 6):
            email = f'lawyer{i}@example.com'
            
            if PolaUser.objects.filter(email=email).exists():
                user = PolaUser.objects.get(email=email)
                users.setdefault('lawyer', []).append(user)
                continue
            
            user = PolaUser.objects.create(
                email=email,
                first_name=f'Lawyer{i}',
                last_name=f'Professional',
                user_role=roles['lawyer'],
                is_active=True,
                date_joined=now - timedelta(days=random.randint(1, 365))
            )
            user.set_password('password123')
            user.save()
            
            Contact.objects.create(
                user=user,
                phone_number=f'+25571234{200+i:04d}',
                phone_is_verified=True
            )
            users.setdefault('lawyer', []).append(user)
        
        self.stdout.write('  Creating law students...')
        # Create law students
        for i in range(1, 11):
            email = f'student{i}@example.com'
            
            if PolaUser.objects.filter(email=email).exists():
                user = PolaUser.objects.get(email=email)
                users.setdefault('law_student', []).append(user)
                continue
            
            user = PolaUser.objects.create(
                email=email,
                first_name=f'Student{i}',
                last_name=f'Law',
                user_role=roles['law_student'],
                is_active=True,
                date_joined=now - timedelta(days=random.randint(1, 365))
            )
            user.set_password('password123')
            user.save()
            
            Contact.objects.create(
                user=user,
                phone_number=f'+25571234{300+i:04d}',
                phone_is_verified=True
            )
            users.setdefault('law_student', []).append(user)
        
        total_users = sum(len(v) for v in users.values())
        self.stdout.write(self.style.SUCCESS(f'  ✓ Loaded {total_users} users'))
        return users

    def create_subscription_plans(self):
        """Create subscription plans"""
        plans_data = [
            {
                'plan_type': 'free_trial',
                'name': 'Free Trial',
                'name_sw': 'Jaribu Bure',
                'description': '24-hour free trial access',
                'description_sw': 'Ufikiaji wa bure wa masaa 24',
                'price': Decimal('0.00'),
                'duration_days': 1,
                'is_active': True
            },
            {
                'plan_type': 'monthly',
                'name': 'Basic Monthly',
                'name_sw': 'Mfumo wa Kila Mwezi',
                'description': 'Monthly subscription with full access',
                'description_sw': 'Usajili wa kila mwezi na ufikiaji kamili',
                'price': Decimal('3000.00'),
                'duration_days': 30,
                'is_active': True
            }
        ]
        
        plans = []
        for plan_data in plans_data:
            plan, created = SubscriptionPlan.objects.update_or_create(
                plan_type=plan_data['plan_type'],
                defaults=plan_data
            )
            plans.append(plan)
            if created:
                self.stdout.write(f'  Created plan: {plan.name}')
            else:
                self.stdout.write(f'  Updated plan: {plan.name}')
        
        return plans

    def create_user_subscriptions(self, users, plans):
        """Create user subscriptions"""
        subscriptions = []
        now = timezone.now()
        
        all_users = []
        for user_list in users.values():
            all_users.extend(user_list)
        
        # Create 50 subscriptions
        for i in range(50):
            user = random.choice(all_users)
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
            
            subscription, created = UserSubscription.objects.get_or_create(
                user=user,
                plan=plan,
                start_date=start_date,
                defaults={
                    'end_date': end_date,
                    'status': status,
                    'auto_renew': random.choice([True, False])
                }
            )
            
            if created:
                subscriptions.append(subscription)
        
        self.stdout.write(f'  Created {len(subscriptions)} subscriptions')
        return subscriptions

    def create_call_credit_bundles(self):
        """Create call credit bundles"""
        bundles_data = [
            {'name': '30 Minutes', 'minutes': 30, 'price': Decimal('10000.00'), 'validity_days': 30},
            {'name': '60 Minutes', 'minutes': 60, 'price': Decimal('18000.00'), 'validity_days': 30},
            {'name': '120 Minutes', 'minutes': 120, 'price': Decimal('32000.00'), 'validity_days': 60},
        ]
        
        bundles = []
        for bundle_data in bundles_data:
            bundle, created = CallCreditBundle.objects.update_or_create(
                name=bundle_data['name'],
                defaults=bundle_data
            )
            bundles.append(bundle)
            if created:
                self.stdout.write(f'  Created bundle: {bundle.name}')
            else:
                self.stdout.write(f'  Updated bundle: {bundle.name}')
        
        return bundles

    def create_user_call_credits(self, users, bundles):
        """Create user call credits"""
        credits = []
        now = timezone.now()
        
        all_users = []
        for user_list in users.values():
            all_users.extend(user_list)
        
        # Create 30 call credits
        for i in range(30):
            user = random.choice(all_users)
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
        
        self.stdout.write(f'  Created {len(credits)} call credits')
        return credits

    def create_learning_materials(self, users):
        """Create learning materials"""
        materials = []
        now = timezone.now()
        
        students = users.get('law_student', [])
        if not students:
            return materials
        
        categories = ['notes', 'past_papers', 'tutorials', 'research']
        
        # Create 25 materials
        for i in range(1, 26):
            uploader = random.choice(students)
            
            material = LearningMaterial.objects.create(
                title=f'Legal Material {i}',
                description=f'Study material for legal education {i}',
                uploader=uploader,
                category=random.choice(categories),
                price=Decimal(random.randint(5, 20)) * 1000,
                is_active=True,
                is_approved=random.choice([True, True, False]),  # 66% approved
                created_at=now - timedelta(days=random.randint(0, 90))
            )
            materials.append(material)
        
        self.stdout.write(f'  Created {len(materials)} learning materials')
        return materials

    def create_consultation_bookings(self, users):
        """Create consultation bookings"""
        bookings = []
        now = timezone.now()
        
        citizens = users.get('citizen', [])
        consultants = users.get('advocate', []) + users.get('lawyer', [])
        
        if not citizens or not consultants:
            return bookings
        
        statuses = ['pending', 'confirmed', 'completed', 'cancelled']
        
        # Create 40 bookings
        for i in range(40):
            client = random.choice(citizens)
            consultant = random.choice(consultants)
            
            scheduled_date = now - timedelta(days=random.randint(-10, 30))
            status = random.choice(statuses)
            
            total_amount = Decimal('100000.00')
            platform_commission = total_amount * Decimal('0.4')
            consultant_earnings = total_amount - platform_commission
            
            booking = ConsultationBooking.objects.create(
                client=client,
                consultant=consultant,
                booking_type=random.choice(['mobile', 'physical']),
                status=status,
                scheduled_date=scheduled_date,
                scheduled_duration_minutes=random.choice([30, 60, 90]),
                total_amount=total_amount,
                platform_commission=platform_commission,
                consultant_earnings=consultant_earnings,
                created_at=scheduled_date - timedelta(days=random.randint(1, 7))
            )
            
            if status == 'completed':
                booking.actual_start_time = scheduled_date
                booking.actual_end_time = scheduled_date + timedelta(hours=1)
                booking.actual_duration_minutes = 60
                booking.save()
            
            bookings.append(booking)
        
        self.stdout.write(f'  Created {len(bookings)} consultation bookings')
        return bookings

    def create_payment_transactions(self, users, subscriptions, bookings):
        """Create payment transactions"""
        transactions = []
        now = timezone.now()
        
        transaction_types = ['subscription', 'call_credit', 'consultation', 'material', 'document']
        
        # Create 100 transactions
        for i in range(100):
            all_users = []
            for user_list in users.values():
                all_users.extend(user_list)
            
            user = random.choice(all_users)
            trans_type = random.choice(transaction_types)
            
            amount = Decimal(random.randint(30, 1000)) * 100
            status = random.choices(
                ['completed', 'pending', 'failed'],
                weights=[0.8, 0.1, 0.1]
            )[0]
            
            transaction = PaymentTransaction.objects.create(
                user=user,
                transaction_type=trans_type,
                amount=amount,
                payment_method=random.choice(['azampay', 'mpesa', 'tigopesa']),
                payment_reference=f'PAY{now.timestamp()}{i}',
                status=status,
                created_at=now - timedelta(days=random.randint(0, 60))
            )
            transactions.append(transaction)
        
        self.stdout.write(f'  Created {len(transactions)} payment transactions')
        return transactions

    def create_consultant_earnings(self, users, bookings):
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
        
        self.stdout.write(f'  Created {len(earnings)} consultant earnings')
        return earnings

    def create_uploader_earnings(self, users, materials):
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
        
        self.stdout.write(f'  Created {len(earnings)} uploader earnings')
        return earnings

    def create_disbursements(self, users):
        """Create disbursements"""
        disbursements = []
        now = timezone.now()
        
        consultants = users.get('advocate', []) + users.get('lawyer', [])
        uploaders = users.get('law_student', [])
        
        recipients = consultants + uploaders
        if not recipients:
            return disbursements
        
        admin = PolaUser.objects.filter(is_staff=True).first()
        if not admin:
            return disbursements
        
        statuses = ['pending', 'processing', 'completed', 'failed']
        
        # Create 15 disbursements
        for i in range(15):
            recipient = random.choice(recipients)
            contact = Contact.objects.filter(user=recipient).first()
            
            if not contact:
                continue
            
            status = random.choice(statuses)
            amount = Decimal(random.randint(50, 500)) * 1000
            
            disbursement = Disbursement.objects.create(
                recipient=recipient,
                recipient_phone=contact.phone_number,
                disbursement_type='consultant' if recipient in consultants else 'uploader',
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
        
        self.stdout.write(f'  Created {len(disbursements)} disbursements')
        return disbursements

    def print_summary(self):
        """Print summary of created data"""
        self.stdout.write(self.style.SUCCESS('\n=== DATA SUMMARY ==='))
        self.stdout.write(f'Users: {PolaUser.objects.count()}')
        self.stdout.write(f'Subscription Plans: {SubscriptionPlan.objects.count()}')
        self.stdout.write(f'User Subscriptions: {UserSubscription.objects.count()}')
        self.stdout.write(f'Call Credit Bundles: {CallCreditBundle.objects.count()}')
        self.stdout.write(f'User Call Credits: {UserCallCredit.objects.count()}')
        self.stdout.write(f'Learning Materials: {LearningMaterial.objects.count()}')
        self.stdout.write(f'Consultation Bookings: {ConsultationBooking.objects.count()}')
        self.stdout.write(f'Payment Transactions: {PaymentTransaction.objects.count()}')
        self.stdout.write(f'Consultant Earnings: {ConsultantEarnings.objects.count()}')
        self.stdout.write(f'Uploader Earnings: {UploaderEarnings.objects.count()}')
        self.stdout.write(f'Disbursements: {Disbursement.objects.count()}')
        self.stdout.write(self.style.SUCCESS('===================\n'))

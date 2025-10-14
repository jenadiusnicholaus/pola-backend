from django.core.management.base import BaseCommand
from subscriptions.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Seed initial subscription plans (Free Trial and Monthly)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔄 Seeding subscription plans...'))
        
        # Free Trial Plan - Updated to give users meaningful access to test platform
        free_trial, created = SubscriptionPlan.objects.update_or_create(
            plan_type='free_trial',
            defaults={
                'name': 'Free Trial (24 Hours)',
                'name_sw': 'Majaribio ya Bure (Masaa 24)',
                'description': '''Enjoy 24 hours of free access to explore the platform. 
                Test key features including legal library, ask questions, access forums, 
                and student hub. Limited to 5 questions during trial.''',
                'description_sw': '''Furahia masaa 24 ya upatikanaji wa bure kuchunguza 
                jukwaa. Jaribu vipengele muhimu ikiwa ni pamoja na maktaba ya kisheria, 
                uliza maswali, pata majukwaa, na kituo cha wanafunzi. Maswali 5 tu wakati wa jaribio.''',
                'price': 0.00,
                'duration_days': 1,
                'is_active': True,
                # Give trial users good access to test the platform
                'full_legal_library_access': True,  # ✅ Let them browse legal library
                'monthly_questions_limit': 5,  # ✅ 5 questions to test Q&A feature
                'free_documents_per_month': 0,  # ❌ No free documents (can still purchase)
                'legal_updates': False,  # ❌ No automated updates during trial
                'forum_access': True,  # ✅ Access to forums to engage with community
                'student_hub_access': True,  # ✅ Access to student hub for students
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Created Free Trial plan with testing access'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Updated Free Trial plan with testing access'))
        
        # Monthly Subscription Plan
        monthly, created = SubscriptionPlan.objects.update_or_create(
            plan_type='monthly',
            defaults={
                'name': 'Monthly Subscription',
                'name_sw': 'Usajili wa Kila Mwezi',
                'description': '''Full access to all platform features for 3,000 TZS per month.
                "Kwa Shilingi 100 tu kwa siku, pata mwongozo na msaada wa Kisheria kila wakati"
                For only 100 shillings a day, get legal guidance and assistance anytime.''',
                'description_sw': '''Upatikanaji kamili wa vipengele vyote vya jukwaa kwa 
                Shilingi 3,000 kwa mwezi. "Kwa Shilingi 100 tu kwa siku, pata mwongozo na 
                msaada wa Kisheria kila wakati"''',
                'price': 3000.00,
                'duration_days': 30,
                'is_active': True,
                # Full features for monthly subscription
                'full_legal_library_access': True,
                'monthly_questions_limit': 10,  # 10 questions per month
                'free_documents_per_month': 1,  # 1 free document per month
                'legal_updates': True,
                'forum_access': True,
                'student_hub_access': True,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Created Monthly Subscription plan'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Monthly Subscription plan already exists'))
        
        # Display summary
        self.stdout.write(self.style.SUCCESS('\n📊 Subscription Plans Summary:'))
        self.stdout.write(self.style.SUCCESS('─' * 70))
        
        for plan in SubscriptionPlan.objects.all():
            self.stdout.write(f'\n🎯 {plan.name} ({plan.name_sw})')
            self.stdout.write(f'   Type: {plan.plan_type}')
            self.stdout.write(f'   Price: {plan.price} TZS')
            self.stdout.write(f'   Duration: {plan.duration_days} days')
            self.stdout.write(f'   Full Library: {plan.full_legal_library_access}')
            self.stdout.write(f'   Questions/Month: {plan.monthly_questions_limit}')
            self.stdout.write(f'   Free Docs/Month: {plan.free_documents_per_month}')
            self.stdout.write(f'   Legal Updates: {plan.legal_updates}')
            self.stdout.write(f'   Forum Access: {plan.forum_access}')
            self.stdout.write(f'   Student Hub: {plan.student_hub_access}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Subscription plans seeded successfully!\n'))

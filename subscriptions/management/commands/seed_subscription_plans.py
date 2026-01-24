from django.core.management.base import BaseCommand
from subscriptions.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Seed initial subscription plans (Free Trial and Monthly)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔄 Seeding subscription plans...'))
        
        # Free Trial Plan - Limited access to explore the platform
        # FREE TRIAL RESTRICTIONS:
        # - Can view forums/hubs but NOT comment or reply
        # - Can generate/preview documents but NOT download
        # - Cannot talk to lawyer
        # - Cannot ask questions in Q&A
        # - Cannot book consultations
        # - Limited to 5 legal education subtopics
        # - CAN: Set up account/profile, explore app features
        free_trial, created = SubscriptionPlan.objects.update_or_create(
            plan_type='free_trial',
            defaults={
                'name': 'Free Trial (24 Hours)',
                'name_sw': 'Majaribio ya Bure (Masaa 24)',
                'description': '''Enjoy 24 hours of free access to explore the platform. 
                View all features with limited access. Browse legal library, view forums 
                and hubs (no commenting), preview legal education (5 topics), and generate 
                documents (no download). Subscribe to unlock full features.''',
                'description_sw': '''Furahia masaa 24 ya upatikanaji wa bure kuchunguza jukwaa. 
                Tazama vipengele vyote na ufikiaji mdogo. Vinjari maktaba ya kisheria, ona 
                majukwaa na vituo (bila maoni), tazama elimu ya kisheria (mada 5), na tengeneza 
                nyaraka (bila kupakua). Jiandikishe kufungua vipengele vyote.''',
                'price': 0.00,
                'duration_days': 1,
                'is_active': True,
                # Features - Limited access for trial users
                'full_legal_library_access': True,  # ✅ Can browse legal library
                'monthly_questions_limit': 0,  # ❌ No questions during trial
                'free_documents_per_month': 0,  # ❌ No free documents
                'legal_updates': False,  # ❌ No automated updates
                'forum_access': True,  # ✅ Can VIEW forums (but not comment)
                'student_hub_access': True,  # ✅ Can VIEW student hub (but not comment)
                # Free Trial Restrictions
                'can_comment_in_forums': False,  # ❌ Cannot comment/reply in forums
                'can_download_documents': False,  # ❌ Cannot download templates
                'can_talk_to_lawyer': False,  # ❌ Cannot talk to lawyer
                'can_ask_questions_qa': False,  # ❌ Cannot ask questions
                'can_book_consultation': False,  # ❌ Cannot book consultations
                'legal_ed_subtopics_limit': 5,  # ⚠️ Limited to 5 subtopics
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Created Free Trial plan with exploration access'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Updated Free Trial plan with exploration access'))
        
        # Monthly Subscription Plan - Full access to all features
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
                # Full permissions (not trial restricted)
                'can_comment_in_forums': True,  # ✅ Can comment/reply
                'can_download_documents': True,  # ✅ Can download templates
                'can_talk_to_lawyer': True,  # ✅ Can talk to lawyer
                'can_ask_questions_qa': True,  # ✅ Can ask questions
                'can_book_consultation': True,  # ✅ Can book consultations
                'legal_ed_subtopics_limit': 0,  # ✅ Unlimited (0 = no limit)
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

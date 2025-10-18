"""
Management command to generate Swagger tags documentation
"""

from django.core.management.base import BaseCommand
from django.urls import get_resolver
from rest_framework import viewsets


class Command(BaseCommand):
    help = 'List all API endpoints and their tags for Swagger documentation'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== Swagger Tags Configuration ===\n'))
        
        tag_mapping = {
            # Authentication
            'authentication': '🔐 Authentication',
            'register': '🔐 Authentication',
            'login': '🔐 Authentication',
            'logout': '🔐 Authentication',
            'token': '🔐 Authentication',
            'password': '🔐 Authentication',
            
            # Admin - Users
            'admin-users': '👥 Admin - Users',
            'admin.*user': '👥 Admin - Users',
            
            # Admin - Permissions
            'admin-permissions': '🔐 Admin - Permissions',
            'admin.*permission': '🔐 Admin - Permissions',
            
            # Admin - Subscriptions
            'admin-subscription-plans': '💳 Admin - Subscription Plans',
            'admin.*subscription.*plan': '💳 Admin - Subscription Plans',
            'admin-user-subscriptions': '📊 Admin - User Subscriptions',
            'admin.*subscription.*user': '📊 Admin - User Subscriptions',
            
            # Admin - Consultations
            'admin-pricing': '📞 Admin - Consultations',
            'admin-consultants': '📞 Admin - Consultations',
            'admin-bookings': '📞 Admin - Consultations',
            'admin.*consultation': '📞 Admin - Consultations',
            
            # Admin - Disbursements
            'admin-disbursements': '💸 Admin - Disbursements',
            'admin.*disbursement': '💸 Admin - Disbursements',
            
            # Admin - Earnings
            'admin-earnings': '💰 Admin - Earnings',
            'admin.*earning': '💰 Admin - Earnings',
            
            # Admin - Call Credits
            'admin-call-bundles': '📱 Admin - Call Credits',
            'admin-user-credits': '📱 Admin - Call Credits',
            'admin.*credit': '📱 Admin - Call Credits',
            
            # Admin - Documents
            'admin-materials': '📄 Admin - Documents',
            'admin.*document': '📄 Admin - Documents',
            'admin.*material': '📄 Admin - Documents',
            
            # Admin - Analytics
            'admin-dashboard': '📊 Admin - Analytics',
            'admin-revenue': '📊 Admin - Analytics',
            'admin-users-analytics': '📊 Admin - Analytics',
            'admin-health': '📊 Admin - Analytics',
            'admin.*analytic': '📊 Admin - Analytics',
            
            # Public - Subscriptions
            'subscriptions': '💳 Subscriptions (Public)',
            'subscription.*plan': '💳 Subscriptions (Public)',
            
            # Public - Consultations
            'consultations': '📞 Consultations (Public)',
            'consultation.*booking': '📞 Consultations (Public)',
            'call.*credit': '📞 Consultations (Public)',
            
            # Public - Documents
            'documents': '📄 Documents (Public)',
            'document.*type': '📄 Documents (Public)',
            
            # Public - Materials
            'materials': '📚 Learning Materials (Public)',
            'learning.*material': '📚 Learning Materials (Public)',
            
            # Payments
            'payment': '💰 Payments',
            'transaction': '💰 Payments',
            
            # Lookups
            'lookup': '🔍 Lookups',
            'region': '🔍 Lookups',
            'role': '🔍 Lookups',
            'specialization': '🔍 Lookups',
        }
        
        self.stdout.write('\nTag Mapping:')
        self.stdout.write('-' * 80)
        for pattern, tag in sorted(tag_mapping.items(), key=lambda x: x[1]):
            self.stdout.write(f'{tag:40} <- {pattern}')
        
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('\n✅ Swagger tags configuration displayed\n'))
        self.stdout.write(self.style.WARNING('To apply tags, add them to your ViewSets:\n'))
        self.stdout.write('    class MyViewSet(viewsets.ModelViewSet):')
        self.stdout.write('        swagger_tags = ["Tag Name"]')
        self.stdout.write('')

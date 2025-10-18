"""
Custom Swagger/OpenAPI Configuration
Organizes API endpoints by feature tags for better documentation
"""

from drf_yasg import openapi

# Define tag order and descriptions
SWAGGER_TAGS = [
    {
        'name': '🔐 Authentication',
        'description': 'User registration, login, logout, password management, and profile operations'
    },
    {
        'name': '👤 User Profile',
        'description': 'User profile management and personal information'
    },
    {
        'name': '💳 Subscriptions (Public)',
        'description': 'View subscription plans, subscribe, and manage your subscription'
    },
    {
        'name': '📞 Consultations (Public)',
        'description': 'Book consultations, purchase call credits, and manage bookings'
    },
    {
        'name': '📄 Documents (Public)',
        'description': 'Generate legal documents and access document templates'
    },
    {
        'name': '📚 Learning Materials (Public)',
        'description': 'Browse, purchase, and upload learning materials'
    },
    {
        'name': '💰 Payments',
        'description': 'Payment transactions and payment history'
    },
    {
        'name': '🔍 Lookups',
        'description': 'Get dropdown values for regions, roles, specializations, etc.'
    },
    {
        'name': '👥 Admin - Users',
        'description': 'Admin: Manage users, verification, and user statistics'
    },
    {
        'name': '🔐 Admin - Permissions',
        'description': 'Admin: Manage user permissions and access control'
    },
    {
        'name': '💳 Admin - Subscription Plans',
        'description': 'Admin: Create, update, and manage subscription plans'
    },
    {
        'name': '📊 Admin - User Subscriptions',
        'description': 'Admin: View and manage all user subscriptions'
    },
    {
        'name': '📞 Admin - Consultations',
        'description': 'Admin: Manage consultation bookings, consultants, and pricing'
    },
    {
        'name': '💸 Admin - Disbursements',
        'description': 'Admin: Process payouts to consultants and content uploaders'
    },
    {
        'name': '💰 Admin - Earnings',
        'description': 'Admin: Track and manage consultant/uploader earnings'
    },
    {
        'name': '📱 Admin - Call Credits',
        'description': 'Admin: Manage call credit bundles and user credits'
    },
    {
        'name': '📄 Admin - Documents',
        'description': 'Admin: Manage document types and learning materials'
    },
    {
        'name': '📊 Admin - Analytics',
        'description': 'Admin: Dashboard, revenue, user stats, and platform health'
    },
]

# Swagger settings for better organization
SWAGGER_SETTINGS = {
    'DEFAULT_AUTO_SCHEMA_CLASS': 'drf_yasg.inspectors.SwaggerAutoSchema',
    'USE_SESSION_AUTH': False,
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Enter your JWT token in the format: Bearer <token>'
        }
    },
    'TAGS_SORTER': 'alpha',  # Sort tags alphabetically
    'OPERATIONS_SORTER': 'alpha',  # Sort operations alphabetically
    'DOC_EXPANSION': 'list',  # Expand operations list by default
    'DEEP_LINKING': True,
    'SHOW_EXTENSIONS': False,
}

# Helper function to get tag metadata
def get_tag_metadata():
    """Returns tag metadata for Swagger schema"""
    return [
        {'name': tag['name'], 'description': tag['description']}
        for tag in SWAGGER_TAGS
    ]

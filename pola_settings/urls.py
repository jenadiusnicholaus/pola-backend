"""pola_settings URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

API_VERSION = settings.API_VERSION

# Swagger/OpenAPI schema configuration
schema_view = get_schema_view(
    openapi.Info(
        title="Pola Legal Platform API",
        default_version=API_VERSION,
        description="""
# Pola Legal Platform API Documentation

Welcome to the **Pola Legal Platform API** - A comprehensive legal services platform for Tanzania.

---

## 🎯 Platform Overview

This API serves multiple user types with specialized legal services:

### User Roles
- **👨‍⚖️ Advocates** - Licensed legal practitioners with roll numbers
- **⚖️ Lawyers & Paralegals** - Legal professionals in various organizations
- **🏢 Law Firms** - Legal practice organizations
- **🎓 Law Students & Lecturers** - Academic community members
- **👥 Citizens** - General public users seeking legal assistance

---

## 🔐 Authentication

This API uses **JWT (JSON Web Token)** authentication for secure access.

### Getting Started:
1. **Register** a new account: `POST /api/v1/authentication/register/`
2. **Login** to get tokens: `POST /api/v1/authentication/login/`
3. **Authorize** requests with header: `Authorization: Bearer <access_token>`
4. **Refresh** expired tokens: `POST /api/v1/authentication/token/refresh/`

---

## 📝 User Registration

Registration requires **role-specific information**. Use lookup endpoints to retrieve valid values:

### Available Lookups:
- 🏷️ User roles
- 📍 Regions and districts
- 🎯 Legal specializations
- 🏛️ Place of work
- 🎓 Academic roles
- 📚 Institutions and organizations

**Tip:** Query `/api/v1/lookups/` endpoints before registration to get valid dropdown values.

---

## 🚀 Key Features

### For Consultants (Advocates/Lawyers):
- Register and get verified by admins
- Offer mobile & physical consultations
- Track earnings and statistics
- Manage consultation bookings

### For Clients:
- Purchase consultation vouchers (call credits)
- Book mobile or physical consultations
- Access legal knowledge library
- Generate legal documents
- Subscribe to monthly plans

### For Students:
- Access student hub
- Share study materials
- Earn from uploaded content
- Connect with peers

---

## 💰 Payment Integration

- **Provider:** AzamPay
- **Currency:** TZS (Tanzanian Shillings)
- **Methods:** Mobile Money (Tigo Pesa, Airtel Money, M-Pesa), Bank Transfer

---

## 📚 API Endpoints Categories

1. **Authentication** - User registration, login, profile management
2. **Consultations** - Book and manage legal consultations
3. **Subscriptions** - Monthly platform access plans
4. **Documents** - Generate legal documents
5. **Materials** - Learning resources marketplace
6. **Payments** - Transaction processing
7. **Admin** - Platform management endpoints

---

## 📞 Support

For API support and inquiries, contact: **support@pola.co.tz**
        """,
        terms_of_service="https://www.pola.co.tz/terms/",
        contact=openapi.Contact(
            name="Pola Support Team",
            email="support@pola.co.tz",
            url="https://www.pola.co.tz"
        ),
        license=openapi.License(name="Proprietary License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Authentication
    path('api-auth/', include('rest_framework.urls')),
    
    # API endpoints
    path(f"api/{API_VERSION}/authentication/", include("authentication.urls")),
    path(f"api/{API_VERSION}/admin/auth/", include("authentication.admin_urls")),  # Admin Auth APIs
    path(f"api/{API_VERSION}/admin/", include("subscriptions.admin_urls")),  # Admin Management APIs (NEW)
    path(f"api/{API_VERSION}/subscriptions/", include("subscriptions.urls")),  # Subscription APIs
    path(f"api/{API_VERSION}/lookups/", include("lookups.urls")),
    
    # API Documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),  # Root redirects to Swagger
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

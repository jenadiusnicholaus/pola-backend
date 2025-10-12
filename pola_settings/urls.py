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
        title="Pola API",
        default_version=API_VERSION,
        description="""
        # Pola Legal Platform API Documentation
        
        This API provides endpoints for the Pola legal platform, supporting multiple user roles:
        - **Advocates**: Licensed legal practitioners with roll numbers
        - **Lawyers/Paralegals**: Legal professionals working in various organizations
        - **Law Firms**: Legal practice organizations
        - **Law Students/Lecturers**: Academic users
        - **Citizens**: General public users
        
        ## Authentication
        This API uses JWT (JSON Web Token) authentication. To access protected endpoints:
        1. Register a new user via `/api/v1/authentication/register/`
        2. Login via `/api/v1/authentication/login/` to get access and refresh tokens
        3. Include the access token in the Authorization header: `Bearer <token>`
        4. Refresh the token when expired via `/api/v1/authentication/token/refresh/`
        
        ## User Registration
        Registration requires role-specific fields. Use the lookup endpoints to get valid values for:
        - User roles
        - Regions and districts
        - Specializations
        - Place of work
        - Academic roles
        """,
        terms_of_service="https://www.pola.co.tz/terms/",
        contact=openapi.Contact(email="support@pola.co.tz"),
        license=openapi.License(name="Proprietary"),
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

"""
Swagger/OpenAPI utilities for tagging and documenting API endpoints
"""

from functools import wraps
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


def swagger_tags(*tags):
    """
    Decorator to add Swagger tags to ViewSet classes
    
    Usage:
        @swagger_tags('Admin - Users')
        class UserManagementViewSet(viewsets.ModelViewSet):
            ...
    """
    def decorator(cls):
        cls.swagger_tags = tags
        return cls
    return decorator


def tag_viewset_methods(viewset_class, tag_name):
    """
    Apply swagger tags to all methods in a ViewSet
    
    Usage in ViewSet:
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            tag_viewset_methods(self.__class__, 'Admin - Users')
    """
    # Standard ViewSet methods
    methods = ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']
    
    for method_name in methods:
        if hasattr(viewset_class, method_name):
            method = getattr(viewset_class, method_name)
            if not hasattr(method, '_swagger_auto_schema'):
                setattr(
                    viewset_class,
                    method_name,
                    swagger_auto_schema(tags=[tag_name])(method)
                )
    
    # Also tag @action methods
    for attr_name in dir(viewset_class):
        attr = getattr(viewset_class, attr_name)
        if hasattr(attr, 'mapping') and hasattr(attr, 'detail'):  # It's an @action
            if not hasattr(attr, '_swagger_auto_schema'):
                setattr(
                    viewset_class,
                    attr_name,
                    swagger_auto_schema(tags=[tag_name])(attr)
                )


# Common response schemas for documentation
response_schemas = {
    'success': openapi.Response(
        description='Success',
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'data': openapi.Schema(type=openapi.TYPE_OBJECT),
            }
        )
    ),
    'error': openapi.Response(
        description='Error',
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'error': openapi.Schema(type=openapi.TYPE_STRING),
                'detail': openapi.Schema(type=openapi.TYPE_STRING),
            }
        )
    ),
    'validation_error': openapi.Response(
        description='Validation Error',
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'field_name': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description='List of error messages for this field'
                ),
            }
        )
    ),
    'unauthorized': openapi.Response(
        description='Unauthorized - Authentication required',
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'detail': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    default='Authentication credentials were not provided.'
                ),
            }
        )
    ),
    'forbidden': openapi.Response(
        description='Forbidden - Insufficient permissions',
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'detail': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    default='You do not have permission to perform this action.'
                ),
            }
        )
    ),
    'not_found': openapi.Response(
        description='Not Found',
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'detail': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    default='Not found.'
                ),
            }
        )
    ),
}


# Common query parameters
common_query_params = {
    'page': openapi.Parameter(
        'page',
        openapi.IN_QUERY,
        description='Page number for pagination',
        type=openapi.TYPE_INTEGER,
        default=1
    ),
    'page_size': openapi.Parameter(
        'page_size',
        openapi.IN_QUERY,
        description='Number of items per page',
        type=openapi.TYPE_INTEGER,
        default=10
    ),
    'search': openapi.Parameter(
        'search',
        openapi.IN_QUERY,
        description='Search query',
        type=openapi.TYPE_STRING
    ),
    'ordering': openapi.Parameter(
        'ordering',
        openapi.IN_QUERY,
        description='Order by field (prefix with - for descending)',
        type=openapi.TYPE_STRING
    ),
}

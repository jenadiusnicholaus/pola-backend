"""
Custom Pagination Classes
Extends DRF's built-in pagination for consistent API responses
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class for all verification APIs
    
    Features:
    - Default page size: 20 items
    - Client can control page size via `page_size` query parameter
    - Maximum page size: 100 items
    - Page number via `page` query parameter
    
    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Number of items per page (default: 20, max: 100)
    
    Response format:
    {
        "count": 150,
        "next": "http://api.example.com/verifications/?page=2",
        "previous": null,
        "results": [...]
    }
    
    Usage:
    - Automatically applied to all ViewSets using this pagination class
    - Or manually: page = self.paginate_queryset(queryset)
    """
    page_size = 20
    page_size_query_param = 'page_size'
    page_query_param = 'page'
    max_page_size = 100


class LargeResultsSetPagination(PageNumberPagination):
    """
    Pagination class for endpoints with large datasets
    
    Features:
    - Default page size: 50 items
    - Client can control page size via `page_size` query parameter
    - Maximum page size: 200 items
    
    Use this for bulk operations or admin dashboards
    """
    page_size = 50
    page_size_query_param = 'page_size'
    page_query_param = 'page'
    max_page_size = 200


class SmallResultsSetPagination(PageNumberPagination):
    """
    Pagination class for endpoints with detailed data
    
    Features:
    - Default page size: 10 items
    - Client can control page size via `page_size` query parameter
    - Maximum page size: 50 items
    
    Use this for endpoints returning detailed/nested data
    """
    page_size = 10
    page_size_query_param = 'page_size'
    page_query_param = 'page'
    max_page_size = 50

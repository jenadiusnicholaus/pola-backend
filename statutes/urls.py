from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import StatuteCategoryViewSet, StatuteViewSet

router = DefaultRouter()
router.register(r'categories', StatuteCategoryViewSet, basename='statute-categories')
router.register(r'laws', StatuteViewSet, basename='statute-laws')

urlpatterns = [
    path('', include(router.urls)),
]

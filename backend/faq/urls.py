"""
faq/urls.py — Routing de l'app FAQ Phase 1 (inchangé).

config/urls.py doit contenir :
    path('api/', include('faq.urls')),
    path('api/', include('chatbot.urls')),
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    FAQViewSet,
    FeedbackViewSet,
    faq_stats,
    category_stats,
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'faq',        FAQViewSet,      basename='faq')
router.register(r'feedback',   FeedbackViewSet, basename='feedback')

urlpatterns = [
    path('', include(router.urls)),
    path('stats/',            faq_stats,      name='faq-stats'),
    path('stats/categories/', category_stats, name='category-stats'),
]

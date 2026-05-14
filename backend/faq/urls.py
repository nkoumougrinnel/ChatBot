"""
Routing pour l'API FAQ et Chatbot.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    FAQViewSet,
    FeedbackViewSet,
    ChatbotAskViewSet,
    faq_stats,
    category_stats,
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'faq',        FAQViewSet,      basename='faq')
router.register(r'feedback',   FeedbackViewSet, basename='feedback')
router.register(r'chatbot',    ChatbotAskViewSet, basename='chatbot')

urlpatterns = [

    # ── Phase 1 : routes DRF (inchangées) ────────────────────────────────
    path('', include(router.urls)),
    path('stats/', faq_stats, name='faq-stats'),
    path('stats/categories/', category_stats, name='category-stats'),
]

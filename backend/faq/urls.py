"""
Routing pour l'API FAQ et Chatbot.

Routes enregistrées via DRF router:
- /api/categories/ : GET, POST, PUT, DELETE
- /api/faq/ : GET, POST, PUT, DELETE
- /api/chatbot/ask/ : POST
- /api/feedback/ : GET, POST
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from faq.views import (
    CategoryViewSet,
    FAQViewSet,
    ChatbotAskViewSet,
    FeedbackViewSet,
    health_check,
    faq_stats,
    category_stats,
)

# Initialiser le router DRF
router = DefaultRouter()

# Enregistrer les ViewSets
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'faq', FAQViewSet, basename='faq')
router.register(r'feedback', FeedbackViewSet, basename='feedback')
router.register(r'chatbot', ChatbotAskViewSet, basename='chatbot')

# URLs patterns
urlpatterns = [
    path('', include(router.urls)),
    path('health/', health_check, name='api-health'),
    path('stats/', faq_stats, name='faq-stats'),
    path('stats/categories/', category_stats, name='category-stats'),
]

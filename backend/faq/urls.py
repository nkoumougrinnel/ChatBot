"""
Routing pour l'API FAQ et Chatbot.
<<<<<<< HEAD

Routes enregistrées via DRF router:
- /api/categories/ : GET, POST, PUT, DELETE
- /api/faq/ : GET, POST, PUT, DELETE
- /api/chatbot/ask/ : POST
- /api/feedback/ : GET, POST
=======
>>>>>>> 63bc96bc834531acd7719edd6e3541982a2ed93e
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
<<<<<<< HEAD
from faq.views import (
    CategoryViewSet,
    FAQViewSet,
    ChatbotAskViewSet,
    FeedbackViewSet,
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
=======
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

    # ── Phase 1 : routes DRF (inchangées) ────────────────────────────────
    path('', include(router.urls)),
    path('stats/', faq_stats, name='faq-stats'),
    path('stats/categories/', category_stats, name='category-stats'),
>>>>>>> 63bc96bc834531acd7719edd6e3541982a2ed93e
]

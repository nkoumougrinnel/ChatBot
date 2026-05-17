"""
Routing pour l'API FAQ et Chatbot.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    FAQViewSet,
    FeedbackViewSet,
    # ChatbotAskViewSet, on doit supprimer cette ligne
    faq_stats,
    category_stats,
)
from chatbot.views import (
    ask_chatbot,
    submit_feedback,
    get_stats,
    reload_index,
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'faq',        FAQViewSet,      basename='faq')
router.register(r'feedback',   FeedbackViewSet, basename='feedback')
#router.register(r'chatbot',    ChatbotAskViewSet, basename='chatbot') Supprimer cette ligne

urlpatterns = [

    # ── Phase 1 : routes DRF (inchangées) ────────────────────────────────
    path('', include(router.urls)),
    path('stats/', faq_stats, name='faq-stats'),
    path('stats/categories/', category_stats, name='category-stats'),

    # Phase 2 RAG
    path('chatbot/ask/', ask_chatbot, name='chatbot-ask'),
    path('feedback/', submit_feedback, name='feedback-rag'),
    path('stats/rag/', get_stats, name='stats-rag'),
    path('reload-index/', reload_index, name='reload-index'),
]

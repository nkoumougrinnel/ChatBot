"""
urls.py — Routing pour l'API FAQ et Chatbot SUP'ONE.

Phase 1 (inchangé) :
    GET/POST  /api/categories/              CategoryViewSet
    GET/POST  /api/faq/                     FAQViewSet
    GET/POST  /api/feedback/                FeedbackViewSet
    GET       /api/stats/                   faq_stats
    GET       /api/stats/categories/        category_stats

Phase 2 — Gen3 :
    GET       /api/chatbot/status/          llm_status      (health Ollama + pipeline)
    POST      /api/chatbot/ask/             ask_chatbot     (streaming SSE)
    POST      /api/chatbot/test-llm/        test_llm_latency (debug latence LLM)
    GET       /api/chatbot/reload-index/    reload_index    (recharge FAISS à chaud)
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from faq.views import (
    CategoryViewSet,
    FAQViewSet,
    FeedbackViewSet,
    faq_stats,
    category_stats,
)
from chatbot.views import (
    llm_status,
    ask_chatbot,
    test_llm_latency,
    reload_index,
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'faq',        FAQViewSet,      basename='faq')
router.register(r'feedback',   FeedbackViewSet, basename='feedback')

api_urlpatterns = [
    path('', include(router.urls)),
    path('stats/',            faq_stats,      name='faq-stats'),
    path('stats/categories/', category_stats, name='category-stats'),
    path('chatbot/status/',       llm_status,      name='chatbot-status'),
    path('chatbot/ask/',          ask_chatbot,     name='chatbot-ask'),
    path('chatbot/test-llm/',     test_llm_latency, name='chatbot-test-llm'),
    path('chatbot/reload-index/', reload_index,    name='chatbot-reload-index'),
]

urlpatterns = [
    path('api/', include(api_urlpatterns)),
]

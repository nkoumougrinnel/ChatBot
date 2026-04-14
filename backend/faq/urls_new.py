"""
Routing pour l'API FAQ et Chatbot.

Routes enregistrées via DRF router :
    GET  /api/categories/          → liste + détail catégories
    GET  /api/faq/                 → liste + détail FAQ
    GET  /api/feedback/            → liste feedbacks
    POST /api/feedback/            → soumettre un feedback

Routes Phase 2 ajoutées manuellement (fonctions @api_view) :
    POST /api/chatbot/ask/         → pipeline RAG (MiniLM → FAISS → Phi-3) + streaming SSE
    GET  /api/stats/               → statistiques d'usage + état index FAISS
    POST /api/reload-index/        → rechargement FAISS à chaud sans redémarrer Django
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from faq.views import (
    CategoryViewSet,
    FAQViewSet,
    FeedbackViewSet,
)

# ── Phase 2 : vues RAG (fonctions @api_view, pas des ViewSets) ───────────────
from chatbot.views import (
    ask_chatbot,
    submit_feedback,
    get_stats,
    reload_index,
)

# ── Router DRF (ViewSets Phase 1) ─────────────────────────────────────────────
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'faq',        FAQViewSet,      basename='faq')
router.register(r'feedback',   FeedbackViewSet, basename='feedback')

# NOTE : ChatbotAskViewSet retiré du router — remplacé par ask_chatbot (Phase 2)

# ── URL patterns ──────────────────────────────────────────────────────────────
urlpatterns = [

    # ── Phase 1 : routes DRF (inchangées) ────────────────────────────────
    path('', include(router.urls)),
    path('stats/',            FeedbackViewSet.faq_stats,      name='faq-stats'),
    path('stats/categories/', FeedbackViewSet.category_stats, name='category-stats'),

    # ── Phase 2 : pipeline RAG ────────────────────────────────────────────
    path('chatbot/ask/',   ask_chatbot,    name='chatbot-ask'),
    path('feedback/',      submit_feedback, name='feedback-rag'),
    path('stats/rag/',     get_stats,      name='stats-rag'),
    path('reload-index/',  reload_index,   name='reload-index'),
]

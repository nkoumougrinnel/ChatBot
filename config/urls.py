"""
config/urls.py — Routing principal SUP'ONE.

Phase 1 (FAQ) :
    GET/POST  /api/categories/              CategoryViewSet
    GET/POST  /api/faq/                     FAQViewSet
    GET/POST  /api/feedback/                FeedbackViewSet
    GET       /api/stats/                   faq_stats
    GET       /api/stats/categories/        category_stats

Phase 2 — Gen3 (Chatbot RAG) :
    GET       /api/chatbot/status/          llm_status
    POST      /api/chatbot/ask/             ask_chatbot  (SSE streaming)
    POST      /api/chatbot/test-llm/        test_llm_latency
    GET       /api/chatbot/reload-index/    reload_index

Authentification :
    POST      /api/auth/login/              login_view
    POST      /api/auth/logout/             logout_view
    GET       /api/auth/me/                 me_view
"""

from django.contrib import admin
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
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"faq",        FAQViewSet,      basename="faq")
router.register(r"feedback",   FeedbackViewSet, basename="feedback")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include([
        # FAQ + Feedback
        path("", include(router.urls)),
        path("stats/",            faq_stats,       name="faq-stats"),
        path("stats/categories/", category_stats,  name="category-stats"),

        # Chatbot RAG Gen3
        path("chatbot/status/",       llm_status,       name="chatbot-status"),
        path("chatbot/ask/",          ask_chatbot,       name="chatbot-ask"),
        path("chatbot/test-llm/",     test_llm_latency,  name="chatbot-test-llm"),
        path("chatbot/reload-index/", reload_index,      name="chatbot-reload-index"),

        # Authentification
        path("auth/", include("users.urls")),
    ])),
]

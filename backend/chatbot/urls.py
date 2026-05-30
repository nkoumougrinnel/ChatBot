"""
chatbot/urls.py — Routing de l'app chatbot SUP'ONE Gen3.

Ce fichier ne contient QUE les routes du pipeline RAG Gen3.
Les routes FAQ Phase 1 (categories, faq, feedback, stats) restent
dans faq/urls.py et sont incluses séparément dans config/urls.py.

config/urls.py doit contenir :
    path('api/', include('faq.urls')),
    path('api/', include('chatbot.urls')),
"""

from django.urls import path

from .views import (
    ask_chatbot,
    llm_status,
    reload_index,
    test_llm_latency,
)

urlpatterns = [
    path('chatbot/status/',       llm_status,       name='chatbot-status'),
    path('chatbot/ask/',          ask_chatbot,       name='chatbot-ask'),
    path('chatbot/test-llm/',     test_llm_latency,  name='chatbot-test-llm'),
    path('chatbot/reload-index/', reload_index,      name='chatbot-reload-index'),
]

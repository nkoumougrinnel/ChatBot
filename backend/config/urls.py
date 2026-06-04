"""
Configuration des URL du projet.

- /admin/        : interface d'administration Django
- /api/          : API FAQ Phase 1 (TF-IDF) — voir faq/urls.py
- /api/v2/       : pipeline RAG Gen3 (FAISS + TF-IDF + LLM) — voir chatbot/urls.py

Le pipeline Gen3 dépend de bibliothèques optionnelles (sentence-transformers,
faiss-cpu, google-generativeai). S'il ne peut pas être chargé (dépendance ou
artefact manquant), ses routes ne sont simplement pas montées : l'API Phase 1
reste pleinement fonctionnelle.
"""
import logging

from django.contrib import admin
from django.urls import path, include

logger = logging.getLogger(__name__)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('faq.urls')),
]

# Montage résilient du pipeline Gen3 sous un préfixe versionné distinct,
# afin d'éviter toute collision avec /api/chatbot/ask/ (Phase 1).
try:
    urlpatterns.append(path('api/v2/', include('chatbot.urls')))
    logger.info("Routes Gen3 montees sous /api/v2/")
except Exception as exc:  # pragma: no cover - dépend de l'environnement
    logger.error("Routes Gen3 (chatbot) non montees : %s", exc, exc_info=True)

# backend/chatbot/apps.py

import logging
import os

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class ChatbotConfig(AppConfig):
    name = "chatbot"

    def ready(self):
        """
        Appelé par Django quand toutes les apps sont chargées.
        Précharge les moteurs FAISS et TF-IDF du pipeline Gen3.

        Le chargement est tolérant aux pannes : si les dépendances optionnelles
        ou les artefacts (rag_data/) sont absents, l'application démarre quand
        même (l'API Phase 1 reste fonctionnelle) et l'erreur est journalisée.
        """
        if os.environ.get("HF_OFFLINE", "1") == "1":
            os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
            os.environ.setdefault("HF_DATASETS_OFFLINE", "1")

        # Ne pas charger les modèles lourds pendant les commandes de gestion
        # (migrate, collectstatic, makemigrations, tests…).
        if os.environ.get("RUN_MAIN") == "false":
            return

        try:
            from chatbot.engine import faiss_search, tfidf_fallback
            faiss_search.load_index()
            tfidf_fallback.load()
            logger.info("Pipeline Gen3 chargé (FAISS + TF-IDF).")
        except Exception as exc:
            logger.warning(
                "Pipeline Gen3 non chargé (%s). L'API Phase 1 reste disponible.",
                exc,
            )

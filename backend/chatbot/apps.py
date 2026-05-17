# backend/chatbot/apps.py

from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    name = "chatbot"

    def ready(self):
        """
        Appelé par Django quand toutes les apps sont chargées.
        C'est ici qu'on peut importer les modèles et charger les moteurs.
        """
        import os
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        os.environ.setdefault("HF_DATASETS_OFFLINE",  "1")

        # Charger FAISS et TF-IDF Phase 2
        from chatbot.engine import faiss_search, tfidf_fallback
        faiss_search.load_index()
        tfidf_fallback.load()
import logging
import os
import tempfile
import time
from pathlib import Path

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class FaqConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'faq'

    def ready(self):
        """
        Initialise le vectorizer TF-IDF et enregistre les signaux au démarrage.

        Un verrou fichier (portable, dans le répertoire temporaire système)
        évite que plusieurs workers Gunicorn entraînent le vectorizer en même
        temps. L'entraînement est ignoré pour le process parent de
        l'autoreloader (RUN_MAIN != 'true').
        """
        # Toujours enregistrer les signaux (chaque worker en a besoin).
        try:
            from faq import signals  # noqa: F401
            logger.info("Signaux FAQ chargés.")
        except Exception as exc:
            logger.warning("Chargement des signaux FAQ échoué : %s", exc)

        # Le process parent de l'autoreloader ne doit pas faire le travail lourd.
        run_main = os.environ.get('RUN_MAIN')
        if run_main is not None and run_main != 'true':
            return

        self._initialize_vectorizer()

    @staticmethod
    def _initialize_vectorizer():
        """Entraîne le vectorizer TF-IDF une seule fois, protégé par un verrou."""
        tmp = Path(tempfile.gettempdir())
        lock_file = tmp / 'faq_vectorizer.lock'
        done_flag = tmp / 'faq_vectorizer_done.flag'

        if done_flag.exists():
            logger.info("Vectorizer TF-IDF déjà initialisé.")
            return

        try:
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
        except FileExistsError:
            # Un autre worker initialise : attendre le flag (max 60s).
            logger.info("Attente de l'initialisation du vectorizer par un autre worker…")
            for _ in range(60):
                if done_flag.exists():
                    logger.info("Vectorizer initialisé par un autre worker.")
                    return
                time.sleep(1)
            logger.warning("Timeout d'attente du vectorizer : nettoyage du verrou.")
            lock_file.unlink(missing_ok=True)
            return

        try:
            from chatbot.vectorization import compute_and_store_vectors
            logger.info("Initialisation du vectorizer TF-IDF…")
            compute_and_store_vectors()
            done_flag.touch()
            logger.info("Vectorizer entraîné et FAQVectors stockés en base.")
        except Exception as exc:
            logger.warning("Initialisation du vectorizer échouée : %s", exc)
        finally:
            lock_file.unlink(missing_ok=True)

"""Utilitaires pour réinitialiser le cache TF-IDF (fichiers temporaires)."""

import tempfile
from pathlib import Path


def reset_vectorizer_files() -> None:
    """Supprime le flag, le verrou et le pickle du vectorizer."""
    tmp = Path(tempfile.gettempdir())
    for name in ('faq_vectorizer_done.flag', 'faq_vectorizer.lock', 'tfidf_vectorizer.pkl'):
        (tmp / name).unlink(missing_ok=True)


def rebuild_faq_vectors() -> int:
    """
    Réentraîne le vectorizer et recalcule tous les FAQVector.
    Retourne le nombre de FAQs vectorisées.
    """
    from chatbot.vectorization import compute_and_store_vectors
    from faq.models import FAQ, FAQVector

    reset_vectorizer_files()
    compute_and_store_vectors()
    return FAQVector.objects.count()

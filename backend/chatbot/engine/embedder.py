"""
embedder.py — Vectorisation des textes avec MiniLM.
Génération 3 : thread-safe, warm-up automatique, cache LRU.
"""

import logging
import os
import threading
import time
from functools import lru_cache

import numpy as np

os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_MODEL_NAME   = "all-MiniLM-L6-v2"
_VECTOR_DIM   = 384
_model        = None
_model_lock   = threading.Lock()
_load_time_s  = 0.0


def _get_model() -> SentenceTransformer:
    """Singleton thread-safe avec double-check lock."""
    global _model, _load_time_s
    if _model is not None:
        return _model
    with _model_lock:
        if _model is None:
            logger.info("[embedder] Chargement de %s...", _MODEL_NAME)
            t0 = time.time()
            _model = SentenceTransformer(_MODEL_NAME)
            _load_time_s = time.time() - t0
            logger.info(
                "[embedder] Modèle chargé en %.1fs — dim=%d",
                _load_time_s, _model.get_sentence_embedding_dimension(),
            )
            # Warm-up : élimine la latence de la première vraie requête
            _model.encode(["warm-up"], convert_to_numpy=True, normalize_embeddings=True)
            logger.info("[embedder] Warm-up terminé.")
    return _model


def encode(text: str) -> np.ndarray:
    """Transforme un texte en vecteur normalisé (384 dimensions, float32)."""
    if not text or not text.strip():
        return np.zeros(_VECTOR_DIM, dtype=np.float32)
    return _get_model().encode(
        text.strip(),
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).astype(np.float32)


def encode_batch(texts: list[str], batch_size: int = 64) -> np.ndarray:
    """Vectorise une liste de textes en une seule passe."""
    if not texts:
        return np.empty((0, _VECTOR_DIM), dtype=np.float32)
    clean = [t.strip() if t and t.strip() else " " for t in texts]
    return _get_model().encode(
        clean,
        convert_to_numpy=True,
        normalize_embeddings=True,
        batch_size=batch_size,
        show_progress_bar=len(texts) > 200,
    ).astype(np.float32)


@lru_cache(maxsize=512)
def encode_cached(text: str) -> tuple:
    """
    Version cachée de encode() pour les textes fréquemment répétés.
    Retourne un tuple (hashable) — utilisé par le cache sémantique de rag_pipeline.
    """
    return tuple(encode(text).tolist())


def get_dimension() -> int:
    return _get_model().get_sentence_embedding_dimension()


if __name__ == "__main__":
    vec = encode("Test phrase")
    print(f"Vecteur shape: {vec.shape}, norme: {np.linalg.norm(vec):.4f}")

    # Test cache
    encode_cached("Test cache")
    encode_cached("Test cache")
    print(f"Cache info : {encode_cached.cache_info()}")

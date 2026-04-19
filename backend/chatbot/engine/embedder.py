"""
embedder.py — Chargement du modèle MiniLM et vectorisation des textes.

Charge all-MiniLM-L6-v2 une seule fois au démarrage du serveur.
Expose encode(text) -> np.ndarray (vecteur de dimension 384).

Dépendance : pip install sentence-transformers
"""

import numpy as np

import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
from sentence_transformers import SentenceTransformer

# -------------------------------------------------------------------
# Chargement du modèle (une seule fois, au premier import du module)
# -------------------------------------------------------------------
_MODEL_NAME = "all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Retourne le modèle, en le chargeant si nécessaire (lazy singleton)."""
    global _model
    if _model is None:
        print(f"[embedder] Chargement du modèle '{_MODEL_NAME}'...")
        _model = SentenceTransformer(_MODEL_NAME)
        print(f"[embedder] Modèle chargé. Dimension des vecteurs : {_model.get_embedding_dimension()}")
    return _model


def encode(text: str) -> np.ndarray:
    """
    Transforme un texte en vecteur de 384 nombres (float32).

    Args:
        text: La phrase ou question à vectoriser.

    Returns:
        np.ndarray de forme (384,), dtype float32.
    """
    model = _get_model()
    vector = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    return vector.astype(np.float32)


def encode_batch(texts: list[str]) -> np.ndarray:
    """
    Vectorise une liste de textes en une seule passe (plus efficace).

    Args:
        texts: Liste de phrases/questions.

    Returns:
        np.ndarray de forme (len(texts), 384), dtype float32.
    """
    if not texts:
        return np.empty((0, 384), dtype=np.float32)
    model = _get_model()
    vectors = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True, batch_size=64, show_progress_bar=False)
    return vectors.astype(np.float32)


def get_dimension() -> int:
    """Retourne la dimension des vecteurs produits par le modèle (384)."""
    return _get_model().get_sentence_embedding_dimension()


# -------------------------------------------------------------------
# Test rapide (exécutable directement : python embedder.py)
# -------------------------------------------------------------------
if __name__ == "__main__":
    import time

    phrases = [
        "C'est combien pour s'inscrire ?",
        "Quels sont les frais de scolarité ?",
        "Comment intégrer SUP'PTIC ?",
    ]

    print("\n=== Test embedder.py ===")
    for phrase in phrases:
        t0 = time.time()
        vec = encode(phrase)
        elapsed_ms = (time.time() - t0) * 1000
        print(f"  '{phrase[:45]}' → vecteur shape={vec.shape}, dtype={vec.dtype}, norme={np.linalg.norm(vec):.4f} ({elapsed_ms:.1f} ms)")

    # Similarité cosinus entre les deux premières phrases (doivent être proches)
    v1 = encode(phrases[0])
    v2 = encode(phrases[1])
    sim = float(np.dot(v1, v2))  # vecteurs normalisés → dot product = cosine sim
    print(f"\nSimilarité cosinus entre '{phrases[0]}' et '{phrases[1]}' : {sim:.4f}")
    print("(Attendu > 0.70 pour deux phrases de sens proche)\n")

"""
embedder.py — Vectorisation des textes avec MiniLM.
"""

import numpy as np
import os

os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"
_model = None


def _get_model():
    global _model
    if _model is None:
        print(f"[embedder] Chargement de {_MODEL_NAME}...")
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def encode(text: str) -> np.ndarray:
    """Transforme un texte en vecteur (384 dimensions)."""
    model = _get_model()
    return model.encode(text, convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)


def encode_batch(texts: list[str]) -> np.ndarray:
    """Vectorise une liste de textes."""
    if not texts:
        return np.empty((0, 384), dtype=np.float32)
    model = _get_model()
    return model.encode(texts, convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)


if __name__ == "__main__":
    vec = encode("Test phrase")
    print(f"Vecteur shape: {vec.shape}, norme: {np.linalg.norm(vec):.4f}")
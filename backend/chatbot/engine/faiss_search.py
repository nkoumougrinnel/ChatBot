"""
faiss_search.py — Recherche vectorielle avec FAISS.
"""

import json
from pathlib import Path

import faiss
import numpy as np

_BASE_DIR = Path(__file__).resolve().parent.parent.parent
_RAG_DATA_DIR = _BASE_DIR / "rag_data"
_INDEX_PATH = _RAG_DATA_DIR / "index.bin"
_METADATA_PATH = _RAG_DATA_DIR / "metadata.json"

_index = None
_metadata = []


def load_index():
    """Charge l'index FAISS au démarrage."""
    global _index, _metadata
    
    if not _INDEX_PATH.exists():
        print(f"[faiss_search] Index introuvable: {_INDEX_PATH}")
        return
    
    _index = faiss.read_index(str(_INDEX_PATH))
    with open(_METADATA_PATH, "r", encoding="utf-8") as f:
        _metadata = json.load(f)
    
    print(f"[faiss_search] Chargé: {_index.ntotal} vecteurs")


def is_loaded():
    return _index is not None


def search(query_vec: np.ndarray, k: int = 3) -> list[tuple[int, float]]:
    """Cherche les k vecteurs les plus proches."""
    if _index is None:
        return []
    
    query = np.expand_dims(query_vec, axis=0).astype(np.float32)
    distances, indices = _index.search(query, min(k, _index.ntotal))
    
    return [(int(idx), float(dist)) for dist, idx in zip(distances[0], indices[0]) if idx != -1]


def search_with_metadata(query_vec: np.ndarray, k: int = 3) -> list[dict]:
    """Recherche avec métadonnées."""
    results = []
    for meta_id, score in search(query_vec, k):
        if 0 <= meta_id < len(_metadata):
            meta = _metadata[meta_id]
            results.append({
                "score": score,
                "response": meta.get("response", ""),
                "example": meta.get("example", ""),
                "categorie": meta.get("categorie", ""),
                "source": meta.get("source", ""),
            })
    return results


if __name__ == "__main__":
    load_index()
    print(f"Statut: chargé={_index is not None}")
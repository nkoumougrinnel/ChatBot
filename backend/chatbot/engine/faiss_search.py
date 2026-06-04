"""
faiss_search.py — Recherche vectorielle avec FAISS.
Génération 3 : thread-safe, seuils exportés, confidence_level, reload à chaud.
"""

import json
import logging
import os
import threading
from pathlib import Path

import faiss
import numpy as np

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Chemins
# -------------------------------------------------------------------
_BASE_DIR      = Path(__file__).resolve().parent.parent.parent
_RAG_DATA_DIR  = Path(os.environ.get("RAG_DATA_DIR", _BASE_DIR / "rag_data"))
_INDEX_PATH    = _RAG_DATA_DIR / "index.bin"
_METADATA_PATH = _RAG_DATA_DIR / "metadata.json"

# -------------------------------------------------------------------
# Seuils de confiance — importés par rag_pipeline.py
# -------------------------------------------------------------------
SCORE_DIRECT = float(os.environ.get("SCORE_DIRECT", "0.52"))  # Niveau 2 → réponse directe FAISS
SCORE_LLM    = float(os.environ.get("SCORE_LLM",    "0.30"))  # Zone TF-IDF / repli FAISS

# -------------------------------------------------------------------
# État interne (thread-safe)
# -------------------------------------------------------------------
_index    = None
_metadata = []
_lock     = threading.Lock()


# -------------------------------------------------------------------
# Chargement
# -------------------------------------------------------------------
def load_index(
    index_path:    Path = _INDEX_PATH,
    metadata_path: Path = _METADATA_PATH,
) -> None:
    """Charge l'index FAISS au démarrage (thread-safe)."""
    global _index, _metadata

    with _lock:
        if not index_path.exists():
            logger.warning("[faiss_search] Index introuvable : '%s'", index_path)
            return

        if not metadata_path.exists():
            raise FileNotFoundError(f"[faiss_search] metadata.json introuvable : '{metadata_path}'")

        _index = faiss.read_index(str(index_path))
        with open(metadata_path, "r", encoding="utf-8") as f:
            _metadata = json.load(f)

        logger.info("[faiss_search] Chargé : %d vecteurs | %d métadonnées", _index.ntotal, len(_metadata))


def reload_index(
    index_path:    Path = _INDEX_PATH,
    metadata_path: Path = _METADATA_PATH,
) -> None:
    """Recharge l'index à chaud sans redémarrer Django."""
    global _index, _metadata
    with _lock:
        _index    = None
        _metadata = []
    load_index(index_path, metadata_path)
    logger.info("[faiss_search] Index rechargé à chaud.")


def is_loaded() -> bool:
    return _index is not None


# -------------------------------------------------------------------
# Recherche
# -------------------------------------------------------------------
def search(query_vec: np.ndarray, k: int = 3) -> list[tuple[int, float]]:
    """Cherche les k vecteurs les plus proches. Retourne [(meta_id, score)]."""
    if _index is None:
        return []

    query = np.expand_dims(query_vec, axis=0).astype(np.float32)
    k_eff = min(k + 2, _index.ntotal)   # élargissement Gen3 puis filtre
    distances, indices = _index.search(query, k_eff)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        results.append((int(idx), float(dist)))
        if len(results) == k:
            break
    return results


def search_with_metadata(query_vec: np.ndarray, k: int = 3) -> list[dict]:
    """
    Recherche enrichie avec métadonnées et confidence_level.

    confidence_level :
        'direct'  → score >= SCORE_DIRECT  (Niveau 2)
        'llm'     → score >= SCORE_LLM     (Niveau 3 TFIDF)
        'offbase' → score <  SCORE_LLM
    """
    results = []
    for meta_id, score in search(query_vec, k):
        if not (0 <= meta_id < len(_metadata)):
            continue
        meta = _metadata[meta_id]

        if score >= SCORE_DIRECT:
            confidence = "direct"
        elif score >= SCORE_LLM:
            confidence = "llm"
        else:
            confidence = "offbase"

        results.append({
            "vecteur_id":       meta_id,
            "score":            score,
            "response":         meta.get("response", ""),
            "example":          meta.get("example", ""),
            "categorie":        meta.get("categorie", ""),
            "source":           meta.get("source", ""),
            "intent":           meta.get("intent", ""),
            "confidence_level": confidence,
        })
    return results


def get_index_stats() -> dict:
    return {
        "loaded":         is_loaded(),
        "ntotal":         _index.ntotal if _index else 0,
        "dim":            _index.d if _index else 0,
        "metadata_count": len(_metadata),
        "score_direct":   SCORE_DIRECT,
        "score_llm":      SCORE_LLM,
    }


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from embedder import encode

    load_index()
    print(f"Stats : {get_index_stats()}\n")

    for q in ["C'est combien pour s'inscrire ?", "Quel temps fait-il ?"]:
        results = search_with_metadata(encode(q), k=3)
        if results:
            best = results[0]
            print(f"[{best['confidence_level'].upper():7}] score={best['score']:.4f} | '{q}'")
            print(f"  → [{best['categorie']}] {best['example'][:60]}\n")
        else:
            print(f"[NO RESULT] '{q}'\n")

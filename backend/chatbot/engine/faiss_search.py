"""
faiss_search.py — Gestion de l'index FAISS pour la recherche vectorielle.

Charge index.bin au démarrage (via AppConfig.ready() dans Django).
Expose search(query_vec, k) -> list[tuple[int, float]].

Dépendance : pip install faiss-cpu
"""

import json
import os
from pathlib import Path
from typing import Optional

import faiss
import numpy as np

# -------------------------------------------------------------------
# Chemins par défaut (relatifs à la racine backend/)
# Peut être surchargé via les variables d'environnement Django settings.
# -------------------------------------------------------------------
_BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
RAG_DATA_DIR = Path(os.environ.get("RAG_DATA_DIR", _BASE_DIR / "rag_data"))
INDEX_PATH = RAG_DATA_DIR / "index.bin"
METADATA_PATH = RAG_DATA_DIR / "metadata.json"

# -------------------------------------------------------------------
# État interne (chargé une seule fois)
# -------------------------------------------------------------------
_index: Optional[faiss.Index] = None
_metadata: list[dict] = []


def load_index(index_path: Path = INDEX_PATH, metadata_path: Path = METADATA_PATH) -> None:
    """
    Charge l'index FAISS et les métadonnées depuis le disque.
    Appelé par AppConfig.ready() au démarrage de Django.

    Args:
        index_path:    Chemin vers index.bin
        metadata_path: Chemin vers metadata.json
    """
    global _index, _metadata

    if not index_path.exists():
        print(f"[faiss_search] AVERTISSEMENT : index FAISS introuvable à '{index_path}'. "
              "Lancez scripts/build_index.py pour le générer.")
        return

    if not metadata_path.exists():
        raise FileNotFoundError(f"[faiss_search] metadata.json introuvable à '{metadata_path}'.")

    print(f"[faiss_search] Chargement de l'index FAISS depuis '{index_path}'...")
    _index = faiss.read_index(str(index_path))
    print(f"[faiss_search] Index chargé : {_index.ntotal} vecteurs (dim={_index.d})")

    with open(metadata_path, "r", encoding="utf-8") as f:
        _metadata = json.load(f)
    print(f"[faiss_search] Métadonnées chargées : {len(_metadata)} entrées")


def reload_index(index_path: Path = INDEX_PATH, metadata_path: Path = METADATA_PATH) -> None:
    """
    Recharge l'index FAISS à chaud sans redémarrer Django.
    Appelé par l'endpoint POST /api/reload-index/.
    """
    global _index, _metadata
    _index = None
    _metadata = []
    load_index(index_path, metadata_path)
    print("[faiss_search] Index rechargé à chaud avec succès.")


def is_loaded() -> bool:
    """Retourne True si l'index est chargé en mémoire."""
    return _index is not None


def search(query_vec: np.ndarray, k: int = 3) -> list[tuple[int, float]]:
    """
    Cherche les k vecteurs les plus proches de query_vec dans l'index FAISS.

    Args:
        query_vec: Vecteur de la question (shape (384,), float32, normalisé).
        k:         Nombre de résultats à retourner (default 3).

    Returns:
        Liste de (metadata_id, score) triés par score décroissant.
        score est la similarité cosinus (0.0 à 1.0).
        Retourne [] si l'index n'est pas chargé.
    """
    if _index is None:
        print("[faiss_search] AVERTISSEMENT : index non chargé, recherche impossible.")
        return []

    # FAISS attend un tableau 2D (n_queries, dim)
    query = np.expand_dims(query_vec, axis=0).astype(np.float32)

    k_effective = min(k, _index.ntotal)
    distances, indices = _index.search(query, k_effective)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:  # FAISS retourne -1 si pas assez de vecteurs
            continue
        # Pour IndexFlatIP (produit interne sur vecteurs normalisés) :
        # distance = similarité cosinus directement
        score = float(dist)
        results.append((int(idx), score))

    return results


def get_metadata(metadata_id: int) -> dict:
    """
    Retourne les métadonnées associées à un id vecteur.

    Args:
        metadata_id: Indice retourné par search().

    Returns:
        dict avec les clés : vecteur_id, intent, example, response, categorie, source
        Retourne {} si l'id est invalide.
    """
    if 0 <= metadata_id < len(_metadata):
        return _metadata[metadata_id]
    return {}


def search_with_metadata(query_vec: np.ndarray, k: int = 3) -> list[dict]:
    """
    Recherche et retourne directement les résultats enrichis de métadonnées.

    Args:
        query_vec: Vecteur de la question (shape (384,), float32).
        k:         Nombre de résultats.

    Returns:
        Liste de dicts : {vecteur_id, score, response, example, categorie, source, intent}
    """
    raw_results = search(query_vec, k)
    enriched = []
    for meta_id, score in raw_results:
        meta = get_metadata(meta_id)
        if meta:
            enriched.append({
                "vecteur_id": meta_id,
                "score": score,
                "response": meta.get("response", ""),
                "example": meta.get("example", ""),
                "categorie": meta.get("categorie", ""),
                "source": meta.get("source", ""),
                "intent": meta.get("intent", ""),
            })
    return enriched


def get_index_stats() -> dict:
    """Retourne des statistiques sur l'index actuellement chargé."""
    if _index is None:
        return {"loaded": False, "ntotal": 0, "dim": 0, "metadata_count": 0}
    return {
        "loaded": True,
        "ntotal": _index.ntotal,
        "dim": _index.d,
        "metadata_count": len(_metadata),
    }


# -------------------------------------------------------------------
# Test rapide (exécutable directement : python faiss_search.py)
# -------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from embedder import encode

    print("=== Test faiss_search.py ===")
    load_index()

    stats = get_index_stats()
    if not stats["loaded"]:
        print("Index non disponible — lancez build_index.py d'abord.")
        sys.exit(0)

    print(f"Index chargé : {stats['ntotal']} vecteurs, dim={stats['dim']}\n")

    test_questions = [
        # Admission
        "Comment intégrer SUP'PTIC ?",
        "Quels sont les frais de scolarité ?",
        # Filières
        "Quelles sont les filières disponibles ?",
        "C'est quoi la filière management ? ",
        # Vie pratique
        "Où se trouve SUP'PTIC ?",
        "Comment contacter l'administration ?",
        # Conversationnel
        "Bonjour, tu es qui ?",
        "Merci pour ton aide",
        # Carrières
        "Quels débouchés apres SUP'PTIC ?",
        "Comment rejoindre le club informatique ?",
        "Quel temps fait-il ?",  # hors domaine
    ]

    for question in test_questions:
        vec = encode(question)
        results = search_with_metadata(vec, k=3)
        print(f"Question : '{question}'")
        if results:
            for r in results:
                print(f"  → score={r['score']:.4f} | [{r['categorie']}] {r['example'][:60]}")
        else:
            print("  → Aucun résultat")
        print()

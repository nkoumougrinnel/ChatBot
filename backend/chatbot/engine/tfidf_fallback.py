"""
tfidf_fallback.py — Moteur TF-IDF de la Phase 1 encapsulé comme fallback.

Activé automatiquement par rag_pipeline.py quand le meilleur score FAISS < 0.55.
Expose search(query) -> tuple[str, float, str].

Dépendances : scikit-learn (déjà présent depuis Phase 1)
              pip install scikit-learn
"""

from __future__ import annotations

import json
import os
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# -------------------------------------------------------------------
# Chemins
# -------------------------------------------------------------------
_BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
_TFIDF_CACHE_PATH = Path(
    os.environ.get("TFIDF_CACHE_PATH", _BASE_DIR / "rag_data" / "tfidf_cache.pkl")
)

# Dossier contenant les fichiers JSON de données
_DATA_DIR = Path(os.environ.get("FAQ_DATA_DIR", _BASE_DIR.parent / "data"))

# -------------------------------------------------------------------
# État interne
# -------------------------------------------------------------------
_vectorizer: Optional[TfidfVectorizer] = None
_tfidf_matrix = None  # scipy sparse matrix (n_docs, n_features)
_faq_entries: list[dict] = []  # liste de toutes les entrées FAQ chargées


def _load_faq_from_json(data_dir: Path) -> list[dict]:
    """
    Charge toutes les entrées FAQ depuis les fichiers JSON du dossier data/.
    Compatible avec le format JSON v2 (champs question/reponse_enrichie/exemples)
    et le format Phase 1 (champs question/answer).
    """
    entries = []
    if not data_dir.exists():
        print(f"[tfidf_fallback] Dossier data introuvable : '{data_dir}'")
        return entries

    for json_file in sorted(data_dir.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = [data]
            else:
                continue

            for item in items:
                if not isinstance(item, dict):
                    continue
                # Compatibilité format v1 et v2
                question = item.get("question", "")
                answer = item.get("reponse_enrichie", item.get("answer", item.get("response", "")))
                examples = item.get("exemples", item.get("examples", []))
                categorie = item.get("categorie", "Général")

                if not question or not answer:
                    continue

                # Ajouter l'entrée principale
                entries.append({
                    "question": question,
                    "answer": answer,
                    "categorie": categorie,
                    "source_file": json_file.name,
                })
                # Ajouter chaque variante (exemples) pointant vers la même réponse
                for ex in examples:
                    if ex and isinstance(ex, str):
                        entries.append({
                            "question": ex,
                            "answer": answer,
                            "categorie": categorie,
                            "source_file": json_file.name,
                        })
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[tfidf_fallback] Erreur lecture '{json_file.name}' : {e}")

    return entries


def _build_vectorizer(entries: list[dict]) -> tuple[TfidfVectorizer, any]:
    """Construit le vectoriseur TF-IDF sur les questions de la base."""
    questions = [e["question"] for e in entries]
    vectorizer = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        min_df=1,
        max_features=20000,
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(questions)
    return vectorizer, matrix


def load(data_dir: Path = _DATA_DIR, cache_path: Path = _TFIDF_CACHE_PATH) -> None:
    """
    Initialise le moteur TF-IDF.
    Essaie de charger depuis le cache ; si absent, reconstruit depuis les JSON.

    Args:
        data_dir:   Dossier contenant les fichiers JSON FAQ.
        cache_path: Chemin du cache pickle TF-IDF.
    """
    global _vectorizer, _tfidf_matrix, _faq_entries

    if cache_path.exists():
        print(f"[tfidf_fallback] Chargement du cache TF-IDF depuis '{cache_path}'...")
        with open(cache_path, "rb") as f:
            cached = pickle.load(f)
        _vectorizer = cached["vectorizer"]
        _tfidf_matrix = cached["matrix"]
        _faq_entries = cached["entries"]
        print(f"[tfidf_fallback] Cache chargé : {len(_faq_entries)} entrées.")
        return

    print("[tfidf_fallback] Cache absent — construction depuis les JSON...")
    _faq_entries = _load_faq_from_json(data_dir)
    if not _faq_entries:
        print("[tfidf_fallback] AVERTISSEMENT : aucune entrée FAQ chargée.")
        return

    _vectorizer, _tfidf_matrix = _build_vectorizer(_faq_entries)

    # Sauvegarder le cache
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "wb") as f:
        pickle.dump(
            {"vectorizer": _vectorizer, "matrix": _tfidf_matrix, "entries": _faq_entries},
            f,
        )
    print(f"[tfidf_fallback] {len(_faq_entries)} entrées indexées. Cache sauvegardé.")


def rebuild(data_dir: Path = _DATA_DIR, cache_path: Path = _TFIDF_CACHE_PATH) -> None:
    """Force la reconstruction du cache TF-IDF (ignore le cache existant)."""
    global _vectorizer, _tfidf_matrix, _faq_entries
    if cache_path.exists():
        cache_path.unlink()
        print("[tfidf_fallback] Cache supprimé.")
    load(data_dir, cache_path)


def search(query: str, top_k: int = 1) -> tuple[str, float, str]:
    """
    Cherche la meilleure correspondance TF-IDF pour une question.

    Args:
        query: Question posée par l'étudiant.
        top_k: Nombre de résultats internes (on retourne le meilleur).

    Returns:
        Tuple (réponse, score, method) où :
            - réponse : str — texte de la réponse (ou message d'erreur)
            - score   : float — similarité cosinus (0.0 à 1.0)
            - method  : "TF-IDF"

    Fallback si le moteur n'est pas initialisé : retourne un message d'erreur.
    """
    if _vectorizer is None or _tfidf_matrix is None or not _faq_entries:
        return (
            "Je n'ai pas cette information dans ma base. "
            "Pour plus de détails, contactez le secrétariat de SUP'PTIC.",
            0.0,
            "TF-IDF",
        )

    query_vec = _vectorizer.transform([query])
    scores = cosine_similarity(query_vec, _tfidf_matrix).flatten()
    best_idx = int(np.argmax(scores))
    best_score = float(scores[best_idx])

    if best_score < 0.05:
        return (
            "Je n'ai pas trouvé d'information correspondant à votre question. "
            "Contactez le secrétariat de SUP'PTIC pour plus de détails.",
            best_score,
            "TF-IDF",
        )

    best_entry = _faq_entries[best_idx]
    return (best_entry["answer"], best_score, "TF-IDF")


def search_top_k(query: str, k: int = 3) -> list[dict]:
    """
    Retourne les k meilleures correspondances TF-IDF avec métadonnées complètes.

    Returns:
        Liste de dicts : {answer, score, question, categorie, method}
    """
    if _vectorizer is None or _tfidf_matrix is None or not _faq_entries:
        return []

    query_vec = _vectorizer.transform([query])
    scores = cosine_similarity(query_vec, _tfidf_matrix).flatten()
    top_indices = np.argsort(scores)[::-1][:k]

    results = []
    for idx in top_indices:
        entry = _faq_entries[int(idx)]
        results.append({
            "answer": entry["answer"],
            "score": float(scores[idx]),
            "question": entry["question"],
            "categorie": entry.get("categorie", "Général"),
            "method": "TF-IDF",
        })
    return results


def is_loaded() -> bool:
    """Retourne True si le moteur TF-IDF est initialisé."""
    return _vectorizer is not None and _faq_entries != []


def get_stats() -> dict:
    """Retourne des statistiques sur le moteur TF-IDF."""
    return {
        "loaded": is_loaded(),
        "entries_count": len(_faq_entries),
        "vocab_size": len(_vectorizer.vocabulary_) if _vectorizer else 0,
    }


# -------------------------------------------------------------------
# Test rapide (exécutable directement : python tfidf_fallback.py)
# -------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Test tfidf_fallback.py ===\n")

    load()
    stats = get_stats()
    print(f"Stats : {stats}\n")

    if not is_loaded():
        print("Moteur non chargé — vérifiez le dossier data/.")
        exit(0)

    test_queries = [
        "C'est combien pour s'inscrire ?",
        "Quels sont les frais de scolarité ?",
        "Comment rejoindre le club informatique ?",
        "Quel temps fait-il aujourd'hui ?",     # hors domaine — score < 0.05 attendu
        "tarif scol",
        "comment register suptptic",
    ]

    for q in test_queries:
        answer, score, method = search(q)
        print(f"Q : '{q}'")
        print(f"  → [{method}] score={score:.4f} | {answer[:80]}...")
        print()

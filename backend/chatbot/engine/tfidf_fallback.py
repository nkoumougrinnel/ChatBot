"""
tfidf_fallback.py — Moteur TF-IDF de la Phase 1 encapsulé comme fallback.
Génération 3 : cache thread-safe, chargement paresseux, stats enrichies,
               hint_text pour enrichir le prompt LLM (niveau 3).

Activé par rag_pipeline.py quand le score FAISS < SCORE_DIRECT (0.55).
Expose search(query) -> tuple[str, float, str]
         hint(query)  -> str   (extrait court pour enrichir le prompt LLM)

Dépendances : scikit-learn
"""

from __future__ import annotations

import json
import logging
import os
import pickle
import threading
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Chemins
# -------------------------------------------------------------------
_BASE_DIR        = Path(__file__).resolve().parent.parent.parent  # backend/
_TFIDF_CACHE_PATH = Path(
    os.environ.get("TFIDF_CACHE_PATH", _BASE_DIR / "rag_data" / "tfidf_cache.pkl")
)
def _faq_data_directories() -> list[Path]:
    """Répertoires JSON à indexer pour le fallback TF-IDF Gen3."""
    dirs: list[Path] = []
    env_dir = os.environ.get("FAQ_DATA_DIR")
    if env_dir:
        dirs.append(Path(env_dir))
    dirs.extend([
        _BASE_DIR.parent / "data",
        _BASE_DIR / "data" / "json",
    ])
    seen: set[str] = set()
    out: list[Path] = []
    for d in dirs:
        resolved = str(d.resolve())
        if d.is_dir() and resolved not in seen:
            seen.add(resolved)
            out.append(d)
    return out


_DATA_DIR = _faq_data_directories()[0] if _faq_data_directories() else (_BASE_DIR.parent / "data")

# Seuil en dessous duquel la réponse TF-IDF est jugée non pertinente
_MIN_SCORE = float(os.environ.get("TFIDF_MIN_SCORE", "0.35"))
_TFIDF_BATCH = int(os.environ.get("TFIDF_BATCH_SIZE", "800"))


def _best_similarity(query_vec, matrix) -> tuple[int, float]:
    """Recherche du meilleur score par lots (évite OOM sur grande matrice sparse)."""
    n_rows = matrix.shape[0]
    if n_rows == 0:
        return 0, 0.0

    best_idx = 0
    best_score = -1.0
    batch = max(100, _TFIDF_BATCH)

    for start in range(0, n_rows, batch):
        end = min(start + batch, n_rows)
        chunk = matrix[start:end]
        sims = cosine_similarity(query_vec, chunk).flatten()
        local_i = int(np.argmax(sims))
        local_score = float(sims[local_i])
        if local_score > best_score:
            best_score = local_score
            best_idx = start + local_i

    return best_idx, best_score

# -------------------------------------------------------------------
# État interne (thread-safe)
# -------------------------------------------------------------------
_vectorizer:   Optional[TfidfVectorizer] = None
_tfidf_matrix  = None
_faq_entries:  list[dict] = []
_lock          = threading.Lock()


# -------------------------------------------------------------------
# Chargement des données
# -------------------------------------------------------------------
def _load_faq_from_json(data_dir: Path) -> list[dict]:
    """
    Charge toutes les entrées FAQ depuis les fichiers JSON.
    Compatible format v1 (question/answer) et v2 (question/reponse_enrichie/exemples).
    """
    entries: list[dict] = []
    if not data_dir.exists():
        logger.warning("[tfidf] Dossier data introuvable : '%s'", data_dir)
        return entries

    for json_file in sorted(data_dir.glob("*.json")):
        if json_file.name == "conversational_rules.json":
            continue
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            items = data if isinstance(data, list) else [data]

            for item in items:
                if not isinstance(item, dict):
                    continue
                meta = item.get("metadata") or {}
                categorie = item.get("categorie") or meta.get("categorie", "Général")

                responses = item.get("responses")
                if isinstance(responses, list):
                    answer = (responses[0] or "").strip() if responses else ""
                else:
                    answer = (
                        item.get("reponse_enrichie")
                        or item.get("answer")
                        or item.get("response")
                        or (responses or "")
                    )
                    if isinstance(answer, str):
                        answer = answer.strip()
                    else:
                        answer = ""

                examples = item.get("exemples", item.get("examples", []))
                if examples:
                    for ex in examples:
                        if ex and isinstance(ex, str) and ex.strip() and answer:
                            entries.append({
                                "question":    ex.strip(),
                                "answer":      answer,
                                "categorie":   categorie,
                                "source_file": json_file.name,
                            })
                    continue

                question = item.get("question", "").strip()
                if question and answer:
                    entries.append({
                        "question":    question,
                        "answer":      answer,
                        "categorie":   categorie,
                        "source_file": json_file.name,
                    })

        except (json.JSONDecodeError, KeyError) as exc:
            logger.error("[tfidf] Erreur lecture '%s' : %s", json_file.name, exc)

    return entries


def _build_vectorizer(entries: list[dict]) -> tuple[TfidfVectorizer, object]:
    """Construit le vectoriseur TF-IDF sur les questions de la base."""
    questions = [e["question"] for e in entries]
    vectorizer = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        min_df=1,
        max_features=20_000,
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(questions)
    return vectorizer, matrix


def load(
    data_dir: Path  = _DATA_DIR,
    cache_path: Path = _TFIDF_CACHE_PATH,
) -> None:
    """
    Initialise le moteur TF-IDF (thread-safe).
    Charge depuis le cache si disponible, sinon reconstruit depuis les JSON.
    """
    global _vectorizer, _tfidf_matrix, _faq_entries

    with _lock:
        if _vectorizer is not None:
            return  # déjà chargé

        if cache_path.exists():
            logger.info("[tfidf] Chargement du cache depuis '%s'...", cache_path)
            try:
                with open(cache_path, "rb") as f:
                    cached = pickle.load(f)
                _vectorizer  = cached["vectorizer"]
                _tfidf_matrix = cached["matrix"]
                _faq_entries = cached["entries"]
                logger.info("[tfidf] Cache chargé : %d entrées.", len(_faq_entries))
                return
            except (pickle.UnpicklingError, KeyError) as exc:
                logger.warning("[tfidf] Cache corrompu (%s) — reconstruction...", exc)

        logger.info("[tfidf] Construction depuis les JSON FAQ...")
        _faq_entries = []
        for directory in _faq_data_directories():
            _faq_entries.extend(_load_faq_from_json(directory))
        if not _faq_entries:
            logger.warning("[tfidf] Aucune entrée FAQ chargée.")
            return

        _vectorizer, _tfidf_matrix = _build_vectorizer(_faq_entries)

        # Sauvegarde du cache
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = cache_path.with_suffix(".pkl.tmp")
        with open(tmp, "wb") as f:
            pickle.dump(
                {"vectorizer": _vectorizer, "matrix": _tfidf_matrix, "entries": _faq_entries},
                f, protocol=pickle.HIGHEST_PROTOCOL,
            )
        tmp.rename(cache_path)
        logger.info("[tfidf] %d entrées indexées. Cache sauvegardé.", len(_faq_entries))


def rebuild(
    data_dir: Path  = _DATA_DIR,
    cache_path: Path = _TFIDF_CACHE_PATH,
) -> None:
    """Force la reconstruction du cache (ignore le cache existant)."""
    global _vectorizer, _tfidf_matrix, _faq_entries
    with _lock:
        _vectorizer = None
        _tfidf_matrix = None
        _faq_entries = []
        if cache_path.exists():
            cache_path.unlink()
            logger.info("[tfidf] Cache supprimé.")
    load(data_dir, cache_path)


# -------------------------------------------------------------------
# Recherche
# -------------------------------------------------------------------
def search(query: str) -> tuple[str, float, str]:
    """
    Cherche la meilleure correspondance TF-IDF pour une question.

    Returns:
        (réponse, score, "TF-IDF")
        Si non initialisé ou score < _MIN_SCORE, retourne un message de refus.
    """
    if _vectorizer is None or _tfidf_matrix is None or not _faq_entries:
        return (
            "Je n'ai pas cette information dans ma base. "
            "Pour plus de détails, contactez le secrétariat de SUP'PTIC.",
            0.0,
            "TF-IDF",
        )

    query_vec = _vectorizer.transform([query])
    best_idx, best_score = _best_similarity(query_vec, _tfidf_matrix)

    if best_score < _MIN_SCORE:
        return (
            "Je n'ai pas trouvé d'information correspondant à votre question. "
            "Contactez le secrétariat de SUP'PTIC pour plus de détails.",
            best_score,
            "TF-IDF",
        )

    return (_faq_entries[best_idx]["answer"], best_score, "TF-IDF")


def search_top_k(query: str, k: int = 3) -> list[dict]:
    """
    Retourne les k meilleures correspondances TF-IDF avec métadonnées.

    Returns:
        Liste de dicts : {answer, score, question, categorie, method}
    """
    if _vectorizer is None or _tfidf_matrix is None or not _faq_entries:
        return []

    query_vec = _vectorizer.transform([query])
    n_rows = _tfidf_matrix.shape[0]
    batch = max(100, _TFIDF_BATCH)
    top_scores: list[tuple[float, int]] = []

    for start in range(0, n_rows, batch):
        end = min(start + batch, n_rows)
        sims = cosine_similarity(query_vec, _tfidf_matrix[start:end]).flatten()
        for local_i, score in enumerate(sims):
            top_scores.append((float(score), start + local_i))

    top_scores.sort(key=lambda x: x[0], reverse=True)
    top_indices = [idx for _, idx in top_scores[:k]]
    scores_map = {idx: sc for sc, idx in top_scores}

    return [
        {
            "answer":    _faq_entries[int(i)]["answer"],
            "score":     float(scores_map.get(i, 0.0)),
            "question":  _faq_entries[int(i)]["question"],
            "categorie": _faq_entries[int(i)].get("categorie", "Général"),
            "method":    "TF-IDF",
        }
        for i in top_indices
    ]


def hint(query: str, max_chars: int = 300) -> str:
    """
    Gen3 : retourne un extrait court de la meilleure réponse TF-IDF,
    utilisé pour enrichir le prompt LLM quand FAISS n'est pas confiant.

    Returns:
        Str vide si non chargé ou score trop bas.
    """
    answer, score, _ = search(query)
    if score < _MIN_SCORE:
        return ""
    return answer[:max_chars] + ("…" if len(answer) > max_chars else "")


def is_loaded() -> bool:
    """Retourne True si le moteur TF-IDF est initialisé."""
    return _vectorizer is not None and bool(_faq_entries)


def get_stats() -> dict:
    """Retourne des statistiques sur le moteur TF-IDF."""
    return {
        "loaded":        is_loaded(),
        "entries_count": len(_faq_entries),
        "vocab_size":    len(_vectorizer.vocabulary_) if _vectorizer else 0,
        "min_score":     _MIN_SCORE,
    }


# -------------------------------------------------------------------
# Test rapide (python tfidf_fallback.py)
# -------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("=== Test tfidf_fallback.py — Génération 3 ===\n")

    load()
    print(f"Stats : {get_stats()}\n")

    if not is_loaded():
        print("Moteur non chargé — vérifiez le dossier data/.")
        exit(0)

    test_queries = [
        "C'est combien pour s'inscrire ?",
        "Quels sont les frais de scolarité ?",
        "Comment rejoindre le club informatique ?",
        "Quel temps fait-il aujourd'hui ?",
        "tarif scol",
        "comment register suptptic",
    ]

    for q in test_queries:
        answer, score, method = search(q)
        h = hint(q)
        print(f"Q : '{q}'")
        print(f"  [{method}] score={score:.4f} | {answer[:80]}")
        print(f"  hint       : '{h[:60]}'")
        print()

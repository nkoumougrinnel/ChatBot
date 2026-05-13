"""
tfidf_fallback.py — Moteur TF-IDF de la Phase 1 encapsulé comme fallback.

Activé automatiquement par rag_pipeline.py quand le meilleur score FAISS < 0.55.
Expose search(query) -> tuple[str, float, str].

Corrections apportées :
    - Lecture UTF-8 with BOM (utf-8-sig) pour les fichiers Windows
    - Réencodage automatique Latin-1 → UTF-8 pour les données corrompues
    - Compatibilité format Phase 1 (responses/examples/metadata)
      ET format Phase 2 (reponse_enrichie/exemples/valide)

Dépendances : pip install scikit-learn
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
_BASE_DIR     = Path(__file__).resolve().parent.parent.parent  # backend/
_TFIDF_CACHE  = Path(os.environ.get("TFIDF_CACHE_PATH",
                     _BASE_DIR / "rag_data" / "tfidf_cache.pkl"))
_DATA_DIR     = Path(os.environ.get("FAQ_DATA_DIR",
                     _BASE_DIR.parent / "data"))

# -------------------------------------------------------------------
# État interne
# -------------------------------------------------------------------
_vectorizer: Optional[TfidfVectorizer] = None
_tfidf_matrix = None
_faq_entries: list[dict] = []


# -------------------------------------------------------------------
# Utilitaire — correction encodage Latin-1 → UTF-8
# -------------------------------------------------------------------
def _fix_encoding(text: str) -> str:
    """
    Corrige les chaînes mal encodées (Latin-1 lues comme UTF-8).
    Exemple : "Ã©cole" → "école"
    """
    if not isinstance(text, str):
        return text
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text  # déjà propre ou non récupérable


def _fix_entry(entry: dict) -> dict:
    """Applique _fix_encoding récursivement sur toutes les valeurs string du dict."""
    result = {}
    for key, value in entry.items():
        if isinstance(value, str):
            result[key] = _fix_encoding(value)
        elif isinstance(value, list):
            result[key] = [
                _fix_encoding(v) if isinstance(v, str) else v
                for v in value
            ]
        elif isinstance(value, dict):
            result[key] = _fix_entry(value)
        else:
            result[key] = value
    return result


# -------------------------------------------------------------------
# Chargement des fichiers JSON (format Phase 1 ET Phase 2)
# -------------------------------------------------------------------
def _open_json(path: Path) -> list[dict]:
    """
    Ouvre un fichier JSON en gérant :
        - UTF-8 with BOM (encodage Windows) → utf-8-sig
        - UTF-8 standard → utf-8
        - Latin-1 / CP1252 → latin-1 en dernier recours
    """
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with open(path, "r", encoding=encoding) as f:
                data = json.load(f)
            return data if isinstance(data, list) else [data]
        except UnicodeDecodeError:
            continue
        except json.JSONDecodeError as e:
            print(f"[tfidf_fallback] JSON invalide dans '{path.name}' : {e}")
            return []
    print(f"[tfidf_fallback] Impossible de lire '{path.name}' (encodages épuisés).")
    return []


def _parse_entry(item: dict) -> dict | None:
    """
    Normalise une entrée JSON vers le format interne commun.

    Supporte :
        Format Phase 2 : reponse_enrichie / exemples / valide
        Format Phase 1 : responses / examples / metadata
    """
    if not isinstance(item, dict):
        return None

    # ── Réponse ──────────────────────────────────────────────────────
    answer = (
        item.get("reponse_enrichie")          # Phase 2
        or item.get("answer")
        or item.get("response")
        or (item["responses"][0] if item.get("responses") else None)  # Phase 1
        or ""
    ).strip()

    # ── Question principale ───────────────────────────────────────────
    question = item.get("question", "").strip()
    if not question:
        # Phase 1 : prendre le premier exemple comme question
        examples_raw = item.get("examples", item.get("exemples", []))
        question = examples_raw[0].strip() if examples_raw else ""

    if not question or not answer:
        return None

    # ── Exemples ─────────────────────────────────────────────────────
    examples = item.get("exemples", item.get("examples", []))
    if not isinstance(examples, list):
        examples = []

    # ── Catégorie / source ────────────────────────────────────────────
    metadata = item.get("metadata", {})
    categorie = (
        item.get("categorie")
        or metadata.get("categorie", "Général")
    )
    source = (
        item.get("source", "")
        or metadata.get("source", "")
        or (", ".join(item["sources"]) if isinstance(item.get("sources"), list) else "")
    )

    # ── Filtre Phase 2 : ignorer les entrées non validées ─────────────
    # (Phase 1 n'a pas ce champ → on accepte par défaut)
    valide = item.get("valide", True)
    if valide is False:
        return None

    return {
        "question":  question,
        "answer":    answer,
        "examples":  [e.strip() for e in examples if isinstance(e, str) and e.strip()],
        "categorie": categorie,
        "source":    source,
    }


def _load_faq_from_json(data_dir: Path) -> list[dict]:
    """Charge toutes les entrées FAQ depuis les fichiers JSON du dossier data/."""
    entries = []

    if not data_dir.exists():
        print(f"[tfidf_fallback] Dossier data introuvable : '{data_dir}'")
        return entries

    # Chercher faq_*.json en priorité, sinon tous les .json
    json_files = sorted(data_dir.glob("faq_*.json"))
    if not json_files:
        json_files = sorted(data_dir.glob("*.json"))

    for json_file in json_files:
        raw_items = _open_json(json_file)
        file_count = 0
        for item in raw_items:
            # Corriger l'encodage avant de parser
            item = _fix_entry(item)
            parsed = _parse_entry(item)
            if not parsed:
                continue

            # Entrée principale
            entries.append(parsed)

            # Variantes (exemples) → pointent vers la même réponse
            seen = {parsed["question"].lower()}
            for ex in parsed["examples"]:
                key = ex.lower()
                if key not in seen:
                    seen.add(key)
                    entries.append({
                        "question":  ex,
                        "answer":    parsed["answer"],
                        "examples":  [],
                        "categorie": parsed["categorie"],
                        "source":    parsed["source"],
                    })
            file_count += 1

        print(f"[tfidf_fallback]   {json_file.name} ({json_file.stat().st_size // 1024} Ko)"
              f" → {file_count} entrées chargées")

    return entries


# -------------------------------------------------------------------
# Construction du vectoriseur TF-IDF
# -------------------------------------------------------------------
def _build_vectorizer(entries: list[dict]):
    questions  = [e["question"] for e in entries]
    vectorizer = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        min_df=1,
        max_features=20_000,
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(questions)
    return vectorizer, matrix


# -------------------------------------------------------------------
# API publique
# -------------------------------------------------------------------
def load(data_dir: Path = _DATA_DIR, cache_path: Path = _TFIDF_CACHE) -> None:
    """
    Initialise le moteur TF-IDF.
    Charge depuis le cache pickle si disponible, sinon reconstruit depuis les JSON.
    """
    global _vectorizer, _tfidf_matrix, _faq_entries

    if cache_path.exists():
        print(f"[tfidf_fallback] Chargement du cache '{cache_path}'...")
        with open(cache_path, "rb") as f:
            cached = pickle.load(f)
        _vectorizer  = cached["vectorizer"]
        _tfidf_matrix = cached["matrix"]
        _faq_entries  = cached["entries"]
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
            {"vectorizer": _vectorizer,
             "matrix":     _tfidf_matrix,
             "entries":    _faq_entries},
            f,
        )
    print(f"[tfidf_fallback] {len(_faq_entries)} entrées indexées. "
          f"Cache sauvegardé → '{cache_path}'")


def rebuild(data_dir: Path = _DATA_DIR, cache_path: Path = _TFIDF_CACHE) -> None:
    """Force la reconstruction complète du cache."""
    global _vectorizer, _tfidf_matrix, _faq_entries
    if cache_path.exists():
        cache_path.unlink()
    load(data_dir, cache_path)


def search(query: str, top_k: int = 1) -> tuple[str, float, str]:
    """
    Retourne (réponse, score, "TF-IDF") pour la question posée.
    Retourne un message d'indirection si le moteur n'est pas chargé ou si
    le score est trop faible.
    """
    if _vectorizer is None or _tfidf_matrix is None or not _faq_entries:
        return (
            "Je n'ai pas cette information dans ma base. "
            "Pour plus de détails, contactez le secrétariat de SUP'PTIC.",
            0.0,
            "TF-IDF",
        )

    query_vec = _vectorizer.transform([query])
    scores    = cosine_similarity(query_vec, _tfidf_matrix).flatten()
    best_idx  = int(np.argmax(scores))
    best_score = float(scores[best_idx])

    if best_score < 0.05:
        return (
            "Je n'ai pas trouvé d'information correspondant à votre question. "
            "Contactez le secrétariat de SUP'PTIC pour plus de détails.",
            best_score,
            "TF-IDF",
        )

    return (_faq_entries[best_idx]["answer"], best_score, "TF-IDF")


def search_top_k(query: str, k: int = 3) -> list[dict]:
    """Retourne les k meilleures correspondances avec métadonnées."""
    if _vectorizer is None or _tfidf_matrix is None or not _faq_entries:
        return []

    query_vec  = _vectorizer.transform([query])
    scores     = cosine_similarity(query_vec, _tfidf_matrix).flatten()
    top_indices = np.argsort(scores)[::-1][:k]

    return [
        {
            "answer":    _faq_entries[int(i)]["answer"],
            "score":     float(scores[i]),
            "question":  _faq_entries[int(i)]["question"],
            "categorie": _faq_entries[int(i)].get("categorie", "Général"),
            "method":    "TF-IDF",
        }
        for i in top_indices
    ]


def is_loaded() -> bool:
    return _vectorizer is not None and bool(_faq_entries)


def get_stats() -> dict:
    return {
        "loaded":        is_loaded(),
        "entries_count": len(_faq_entries),
        "vocab_size":    len(_vectorizer.vocabulary_) if _vectorizer else 0,
    }


# -------------------------------------------------------------------
# Test standalone : python tfidf_fallback.py
# -------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Test tfidf_fallback.py ===\n")
    load()
    stats = get_stats()
    print(f"Stats : {stats}\n")

    if not is_loaded():
        print("Moteur non chargé — vérifiez le dossier data/.")
        exit(0)

    tests = [
        "C'est combien pour s'inscrire ?",
        "Quels sont les frais de scolarité ?",
        "Comment rejoindre SUP'PTIC ?",
        "Où se trouve l'école ?",
        "Quel temps fait-il ?",
    ]
    for q in tests:
        answer, score, method = search(q)
        print(f"Q : '{q}'")
        print(f"  → [{method}] score={score:.4f} | {answer[:80]}...\n")

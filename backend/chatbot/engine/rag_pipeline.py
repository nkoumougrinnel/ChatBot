"""
rag_pipeline.py — Orchestrateur principal du pipeline RAG avec optimisations.

Flux optimisé :
    question → embed (MiniLM avec cache) → Recherche parallèle FAISS + TF-IDF avec timeout
        → Sélection méthode basée sur score + seuil dynamique
        → si RAG : prompt_builder → LLM (Phi-3)
        → si TF-IDF : réponse directe

Optimisations pour la réactivité :
    - Cache LRU des embeddings (évite recalculs)
    - Parallélisation asynchrone FAISS + TF-IDF avec timeout séparés
    - Seuil dynamique basé sur statistiques des scores récents
    - Chargement paresseux des modèles (via is_loaded())
    - Logging des performances pour monitoring

Expose :
    ask(question, history)          -> dict  (réponse complète)
    ask_stream(question, history)   -> Iterator[str | dict]  (streaming SSE)
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path
from collections.abc import Iterator
from typing import Any
from functools import lru_cache

# --- Résolution du sys.path AVANT les imports ---
_ENGINE_DIR = Path(__file__).resolve().parent
if str(_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENGINE_DIR))

# Imports moteur
try:
    from .embedder import encode
    from .faiss_search import search_with_metadata, is_loaded as faiss_loaded
    from .llm_client import generate, generate_stream
    from .prompt_builder import build_prompt, build_no_context_prompt
    from .tfidf_fallback import search as tfidf_search, is_loaded as tfidf_loaded
except ImportError:
    from embedder import encode
    from faiss_search import search_with_metadata, is_loaded as faiss_loaded
    from llm_client import generate, generate_stream
    from prompt_builder import build_prompt, build_no_context_prompt
    from tfidf_fallback import search as tfidf_search, is_loaded as tfidf_loaded


# -------------------------------------------------------------------
# Configuration optimisée
# -------------------------------------------------------------------
SCORE_HIGH = float(__import__("os").environ.get("RAG_SCORE_HIGH", 0.55))
SCORE_MED = float(__import__("os").environ.get("RAG_SCORE_MED", 0.1))
FAISS_TOP_K = int(__import__("os").environ.get("RAG_TOP_K", 3))
TIMEOUT_FAISS = float(__import__("os").environ.get("RAG_TIMEOUT_FAISS", 1.0))  # secondes
TIMEOUT_TFIDF = float(__import__("os").environ.get("RAG_TIMEOUT_TFIDF", 0.5))  # secondes
# Sur un serveur dédié, augmenter les timeouts pour plus de robustesse :
# TIMEOUT_FAISS = 2.0
# TIMEOUT_TFIDF = 1.0

# Cache des embeddings (LRU pour éviter surcharge mémoire)
@lru_cache(maxsize=500)
# Sur un serveur dédié, augmenter la taille du cache :
# @lru_cache(maxsize=2000)
def _cached_encode(question: str) -> Any:
    """Cache des embeddings pour éviter recalculs identiques."""
    return encode(question)

# Statistiques pour seuil dynamique
_score_history = []
SCORE_WINDOW = 100  # nombre de scores à garder en mémoire

def _update_score_history(score: float):
    """Met à jour l'historique des scores pour calcul du seuil dynamique."""
    _score_history.append(score)
    if len(_score_history) > SCORE_WINDOW:
        _score_history.pop(0)

def _get_dynamic_threshold() -> float:
    """Calcule un seuil dynamique basé sur la moyenne des scores récents."""
    if not _score_history:
        return SCORE_HIGH
    avg_score = sum(_score_history) / len(_score_history)
    # Seuil dynamique : 80% de la moyenne, borné entre 0.3 et 0.8
    dynamic = max(0.3, min(0.8, avg_score * 0.8))
    return dynamic

# Message d'avertissement score moyen
_WARNING_LOW_CONFIDENCE = (
    "⚠️ Cette réponse est approximative — la pertinence est modérée. "
    "Vérifiez auprès du secrétariat si nécessaire.\n\n"
)


def _select_method(best_score: float) -> str:
    """Retourne 'RAG', 'RAG_LOW' ou 'TF-IDF' selon le score FAISS et seuil dynamique."""
    threshold = _get_dynamic_threshold()
    if best_score >= threshold:
        return "RAG"
    elif best_score >= SCORE_MED:
        return "RAG_LOW"
    else:
        return "TF-IDF"


async def _async_faiss_search(query_vec, k: int = FAISS_TOP_K):
    """Recherche FAISS asynchrone avec gestion d'erreurs."""
    if not faiss_loaded():
        return []
    try:
        # Utilise asyncio.to_thread pour rendre FAISS (synchrone) non-bloquant
        contexts = await asyncio.to_thread(search_with_metadata, query_vec, k)
        return contexts
    except Exception as e:
        print(f"[rag_pipeline] Erreur FAISS : {e}")
        return []


async def _async_tfidf_search(question: str):
    """Recherche TF-IDF asynchrone avec gestion d'erreurs."""
    if not tfidf_loaded():
        return None, 0.0, ""
    try:
        result = await asyncio.to_thread(tfidf_search, question)
        return result
    except Exception as e:
        print(f"[rag_pipeline] Erreur TF-IDF : {e}")
        return None, 0.0, ""


async def _parallel_search(question: str, query_vec) -> tuple[list, tuple]:
    """
    Recherche parallèle FAISS et TF-IDF avec timeout séparés.
    Retourne le premier résultat disponible ou les deux si timeout pas atteint.
    """
    # Lancer les deux recherches en parallèle
    faiss_task = asyncio.create_task(_async_faiss_search(query_vec))
    tfidf_task = asyncio.create_task(_async_tfidf_search(question))

    # Attendre FAISS avec timeout
    try:
        contexts = await asyncio.wait_for(faiss_task, timeout=TIMEOUT_FAISS)
    except asyncio.TimeoutError:
        print(f"[rag_pipeline] Timeout FAISS ({TIMEOUT_FAISS}s), annulation")
        contexts = []
        faiss_task.cancel()

    # Attendre TF-IDF avec timeout
    try:
        tfidf_result = await asyncio.wait_for(tfidf_task, timeout=TIMEOUT_TFIDF)
    except asyncio.TimeoutError:
        print(f"[rag_pipeline] Timeout TF-IDF ({TIMEOUT_TFIDF}s), annulation")
        tfidf_result = (None, 0.0, "")
        tfidf_task.cancel()

    return contexts, tfidf_result


def ask(question: str, history: list[dict] | None = None) -> dict:
    """
    Traite une question avec parallélisation asynchrone pour maximiser la réactivité.

    Args:
        question: La question posée par l'étudiant.
        history:  Liste des derniers échanges (optionnel).

    Returns:
        dict avec les clés :
            answer  (str)   : texte de la réponse
            sources (list)  : liste de dicts {question, score, categorie, source}
            method  (str)   : "RAG" ou "TF-IDF"
            best_score (float) : meilleur score FAISS ou TF-IDF
    """
    start_time = time.time()

    # --- Étape 1 : Vectorisation avec cache ---
    query_vec = _cached_encode(question)

    # --- Étape 2 : Recherche parallèle FAISS + TF-IDF ---
    contexts, tfidf_result = asyncio.run(_parallel_search(question, query_vec))

    best_score = contexts[0]["score"] if contexts else 0.0
    _update_score_history(best_score)  # Mise à jour statistiques pour seuil dynamique

    method = _select_method(best_score)

    # --- Étape 3 : Branchement RAG vs TF-IDF ---
    if method in ("RAG", "RAG_LOW"):
        # Construction du prompt
        if contexts:
            prompt = build_prompt(question, contexts, history)
        else:
            prompt = build_no_context_prompt(question)

        # Génération LLM
        raw_answer = generate(prompt)

        # Préfixe d'avertissement si score moyen
        if method == "RAG_LOW":
            answer = _WARNING_LOW_CONFIDENCE + raw_answer
        else:
            answer = raw_answer

        sources = [
            {
                "question": ctx["example"],
                "score": round(ctx["score"], 4),
                "categorie": ctx["categorie"],
                "source": ctx["source"],
            }
            for ctx in contexts[:3]
        ]

    else:
        # Fallback TF-IDF
        tfidf_answer, tfidf_score, _ = tfidf_result
        answer = tfidf_answer or "Désolé, je n'ai pas trouvé de réponse pertinente."
        best_score = tfidf_score
        sources = []  # TF-IDF ne retourne pas de sources structurées

    elapsed = time.time() - start_time
    print(f"[rag_pipeline] Question traitée en {elapsed:.2f}s, méthode: {method}, score: {best_score:.4f}")

    return {
        "answer": answer,
        "sources": sources,
        "method": method.replace("_LOW", ""),  # "RAG" ou "TF-IDF" pour l'API
        "best_score": round(best_score, 4),
    }


def ask_stream(
    question: str,
    history: list[dict] | None = None,
) -> Iterator[str | dict]:
    """
    Traite une question en streaming SSE avec parallélisation.

    Yield order :
        1. dict {"type": "meta", "method": ..., "sources": ..., "best_score": ...}
        2. str (fragments de texte du LLM) — ou str unique si TF-IDF
        3. dict {"type": "done"}

    Compatible avec Django StreamingHttpResponse + text/event-stream.

    Args:
        question: La question posée.
        history:  Historique optionnel.

    Yields:
        str ou dict selon le type d'événement.
    """
    # Vectorisation avec cache
    query_vec = _cached_encode(question)

    # Recherche parallèle
    contexts, tfidf_result = asyncio.run(_parallel_search(question, query_vec))

    best_score = contexts[0]["score"] if contexts else 0.0
    _update_score_history(best_score)

    method = _select_method(best_score)

    sources = [
        {
            "question": ctx["example"],
            "score": round(ctx["score"], 4),
            "categorie": ctx["categorie"],
            "source": ctx["source"],
        }
        for ctx in contexts[:3]
    ] if method in ("RAG", "RAG_LOW") else []

    # Envoi des métadonnées d'abord
    yield {
        "type": "meta",
        "method": method.replace("_LOW", ""),
        "sources": sources,
        "best_score": round(best_score, 4),
        "low_confidence": method == "RAG_LOW",
    }

    # Streaming de la réponse
    if method in ("RAG", "RAG_LOW"):
        if method == "RAG_LOW":
            yield _WARNING_LOW_CONFIDENCE

        if contexts:
            prompt = build_prompt(question, contexts, history)
        else:
            prompt = build_no_context_prompt(question)

        for token in generate_stream(prompt):
            yield token

    else:
        tfidf_answer, _, _ = tfidf_result
        yield tfidf_answer or "Désolé, je n'ai pas trouvé de réponse pertinente."

    yield {"type": "done"}


def build_sse_event(data: Any) -> str:
    """
    Formate un événement pour Django StreamingHttpResponse (text/event-stream).

    Args:
        data: str (token texte) ou dict (métadonnées / done).

    Returns:
        Chaîne formatée SSE : "data: <json>\n\n"
    """
    import json as _json

    if isinstance(data, str):
        payload = _json.dumps({"type": "token", "content": data}, ensure_ascii=False)
    else:
        payload = _json.dumps(data, ensure_ascii=False)
    return f"data: {payload}\n\n"


# -------------------------------------------------------------------
# Test rapide (exécutable directement : python rag_pipeline.py)
# -------------------------------------------------------------------
if __name__ == "__main__":
    import time

    # Initialiser FAISS et TF-IDF
    import faiss_search
    faiss_search.load_index()

    import tfidf_fallback
    tfidf_fallback.load()

    print("=== Test rag_pipeline.py optimisé ===\n")

    test_cases = [
        {
            "question": "C'est combien pour s'inscrire à SUP'PTIC ?",
            "history": None,
        },
        {
            "question": "Et pour les boursiers ?",
            "history": [
                {"role": "user", "content": "C'est combien pour s'inscrire ?"},
                {"role": "assistant", "content": "Les frais sont de 500 000 FCFA par an."},
            ],
        },
        {
            "question": "Quel temps fait-il aujourd'hui ?",  # hors domaine
            "history": None,
        },
    ]

    for tc in test_cases:
        print(f"Question : '{tc['question']}'")
        t0 = time.time()
        result = ask(tc["question"], tc["history"])
        elapsed = time.time() - t0
        print(f"  Méthode : {result['method']} | Score : {result['best_score']:.4f} | {elapsed:.2f}s")
        print(f"  Réponse : {result['answer'][:120]}...")
        if result["sources"]:
            for s in result["sources"]:
                print(f"  Source : [{s['categorie']}] score={s['score']:.4f}")
        print()
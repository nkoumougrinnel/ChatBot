"""
rag_pipeline.py — Orchestrateur principal du pipeline RAG.

Flux :
    question → embed (MiniLM) → FAISS (top-3) → vérifier score
        → si score ≥ 0.55 : prompt_builder → LLM (Phi-3)
        → si score < 0.55 : TF-IDF fallback

Expose :
    ask(question, history)          -> dict  (réponse complète)
    ask_stream(question, history)   -> Iterator[str | dict]  (streaming SSE)
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

# Imports moteur (imports relatifs si exécuté depuis Django,
# imports directs si exécuté en script standalone)
from .embedder import encode
from .faiss_search import search_with_metadata, is_loaded as faiss_loaded
from .llm_client import generate, generate_stream
from .prompt_builder import build_prompt, build_no_context_prompt
from .tfidf_fallback import search as tfidf_search, is_loaded as tfidf_loaded

# -------------------------------------------------------------------
# Seuils de confiance (configurables)
# -------------------------------------------------------------------
SCORE_HIGH = float(__import__("os").environ.get("RAG_SCORE_HIGH", 0.55))
SCORE_MED = float(__import__("os").environ.get("RAG_SCORE_MED", 0.30))
FAISS_TOP_K = int(__import__("os").environ.get("RAG_TOP_K", 3))

# Message d'avertissement score moyen
_WARNING_LOW_CONFIDENCE = (
    "⚠️ Cette réponse est approximative — la pertinence est modérée. "
    "Vérifiez auprès du secrétariat si nécessaire.\n\n"
)


def _select_method(best_score: float) -> str:
    """Retourne 'RAG', 'RAG_LOW' ou 'TF-IDF' selon le score FAISS."""
    if best_score >= SCORE_HIGH:
        return "RAG"
    elif best_score >= SCORE_MED:
        return "RAG_LOW"
    else:
        return "TF-IDF"


def ask(question: str, history: list[dict] | None = None) -> dict:
    """
    Traite une question et retourne une réponse complète (non streamée).

    Args:
        question: La question posée par l'étudiant.
        history:  Liste des derniers échanges (optionnel).

    Returns:
        dict avec les clés :
            answer  (str)   : texte de la réponse
            sources (list)  : liste de dicts {question, score, categorie, source}
            method  (str)   : "RAG", "RAG_LOW" ou "TF-IDF"
            best_score (float) : meilleur score FAISS ou TF-IDF
    """
    # --- Étape 1 : Vectorisation ---
    query_vec = encode(question)

    # --- Étape 2 : Recherche FAISS ---
    contexts = []
    best_score = 0.0

    if faiss_loaded():
        contexts = search_with_metadata(query_vec, k=FAISS_TOP_K)
        if contexts:
            best_score = contexts[0]["score"]

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
        tfidf_answer, tfidf_score, _ = tfidf_search(question)
        answer = tfidf_answer
        best_score = tfidf_score
        sources = []  # TF-IDF ne retourne pas de sources structurées

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
    Traite une question en streaming SSE.

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
    # --- Vectorisation ---
    query_vec = encode(question)

    # --- Recherche FAISS ---
    contexts = []
    best_score = 0.0

    if faiss_loaded():
        contexts = search_with_metadata(query_vec, k=FAISS_TOP_K)
        if contexts:
            best_score = contexts[0]["score"]

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

    # --- Envoi des métadonnées d'abord ---
    yield {
        "type": "meta",
        "method": method.replace("_LOW", ""),
        "sources": sources,
        "best_score": round(best_score, 4),
        "low_confidence": method == "RAG_LOW",
    }

    # --- Streaming de la réponse ---
    if method in ("RAG", "RAG_LOW"):
        if method == "RAG_LOW":
            yield _WARNING_LOW_CONFIDENCE  # avertissement avant le texte LLM

        if contexts:
            prompt = build_prompt(question, contexts, history)
        else:
            prompt = build_no_context_prompt(question)

        for token in generate_stream(prompt):
            yield token

    else:
        # TF-IDF : réponse complète en un seul chunk
        tfidf_answer, tfidf_score, _ = tfidf_search(question)
        yield tfidf_answer

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
    import sys, time
    from pathlib import Path

    # Charger les modules dépendants
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    
    # Imports directs pour mode standalone
    from embedder import encode as _encode
    from faiss_search import load_index
    
    # Initialiser FAISS et TF-IDF
    import faiss_search
    faiss_search.load_index()

    import tfidf_fallback
    tfidf_fallback.load()

    print("=== Test rag_pipeline.py ===\n")

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

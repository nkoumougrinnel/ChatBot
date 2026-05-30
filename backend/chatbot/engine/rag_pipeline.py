"""
rag_pipeline.py — Orchestrateur du pipeline RAG à 4 niveaux (Génération 3 — LLM réactivé).

Niveau 1 — CONV    : regex sur formules conversationnelles → réponse hardcodée   < 1 ms
Niveau 2 — DIRECT  : score FAISS >= 0.55 → réponse FAISS directe, sans LLM      ~150 ms
Niveau 3 — TFIDF   : 0.30 <= score < 0.55 → réponse TF-IDF directe, sans LLM   ~50 ms
Niveau 4 — LLM     : score < 0.30 → top-3 FAISS injectés dans prompt Phi-3      ~15-30 s
           OFFBASE  : score < 0.30 ET Ollama indisponible → refus propre          < 1 ms

Règle Gen3 :
  - Le LLM est appelé UNIQUEMENT quand FAISS ne trouve rien (score < SCORE_LLM).
  - Les top-3 résultats FAISS sont toujours passés en contexte, même avec de faibles scores.
  - Si Ollama est indisponible, le pipeline bascule proprement sur le refus OFFBASE.

Ce module est le seul point d'entrée appelé par views.py.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from functools import lru_cache
from collections.abc import Iterator

import numpy as np

try:
    from .embedder       import encode
    from .faiss_search   import search_with_metadata, SCORE_DIRECT, SCORE_LLM, is_loaded as faiss_is_loaded, get_index_stats
    from .prompt_builder import detect_conv, build_prompt
    from .tfidf_fallback import search as tfidf_search, is_loaded as tfidf_is_loaded, get_stats as tfidf_stats
    from .llm_client     import check_availability, generate, generate_stream
except ImportError:
    from embedder       import encode
    from faiss_search   import search_with_metadata, SCORE_DIRECT, SCORE_LLM, is_loaded as faiss_is_loaded, get_index_stats
    from prompt_builder import detect_conv, build_prompt
    from tfidf_fallback import search as tfidf_search, is_loaded as tfidf_is_loaded, get_stats as tfidf_stats
    from llm_client     import check_availability, generate, generate_stream

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Structure de retour (pour ask())
# -------------------------------------------------------------------
@dataclass
class PipelineResult:
    answer:     str
    level:      str                           # 'conv'|'direct'|'tfidf'|'llm'|'offbase'
    score:      float = 0.0
    latency_ms: float = 0.0
    source:     str = ""
    categorie:  str = ""
    method:     str = ""
    contexts:   list[dict] = field(default_factory=list)


# -------------------------------------------------------------------
# Cache sémantique (LRU sur les questions fréquentes)
# -------------------------------------------------------------------
@lru_cache(maxsize=256)
def _cached_encode(text: str) -> tuple:
    return tuple(encode(text).tolist())


def _get_vec(text: str) -> np.ndarray:
    return np.array(_cached_encode(text), dtype=np.float32)


def _ms(t0: float) -> float:
    return round((time.time() - t0) * 1000, 1)


# -------------------------------------------------------------------
# Construction des événements SSE (spec W3C text/event-stream)
# -------------------------------------------------------------------
def build_sse_event(data: str, event: str | None = None) -> str:
    safe_data = str(data).replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    lines = []
    if event:
        lines.append(f"event: {event.strip()}")
    lines.append(f"data: {safe_data}")
    return "\n".join(lines) + "\n\n"


# -------------------------------------------------------------------
# Pipeline principal — réponse complète (non streamée)
# -------------------------------------------------------------------
def ask(
    question: str,
    history:  list[dict] | None = None,
) -> PipelineResult:
    t0 = time.time()
    question = question.strip()

    if not question:
        return PipelineResult(
            answer="Veuillez saisir une question.",
            level="conv", method="empty", latency_ms=_ms(t0),
        )

    # Niveau 1 — CONV
    conv_answer = detect_conv(question)
    if conv_answer:
        logger.info("[pipeline] CONV '%s'", question[:50])
        return PipelineResult(
            answer=conv_answer, level="conv",
            method="regex", latency_ms=_ms(t0),
        )

    # Vectorisation + FAISS
    query_vec  = _get_vec(question)
    contexts   = search_with_metadata(query_vec, k=3)
    best       = contexts[0] if contexts else None
    best_score = best["score"] if best else 0.0
    logger.info("[pipeline] FAISS score=%.4f | '%s'", best_score, question[:50])

    # Niveau 2 — DIRECT
    if best and best_score >= SCORE_DIRECT:
        answer = best["response"].strip() or (
            "Information disponible mais réponse vide. Contactez le secrétariat."
        )
        logger.info("[pipeline] DIRECT (score=%.4f)", best_score)
        return PipelineResult(
            answer=answer, level="direct", score=best_score,
            latency_ms=_ms(t0), source=best.get("source", ""),
            categorie=best.get("categorie", ""), method="faiss_direct",
            contexts=contexts,
        )

    # Niveau 3 — TFIDF
    if best and best_score >= SCORE_LLM:
        if not tfidf_is_loaded():
            logger.error("[pipeline] ERREUR SYSTÈME : TF-IDF non chargé.")
            raise RuntimeError(
                "Pipeline Gen3 mal initialisé : TF-IDF non chargé. "
                "Appelez tfidf_fallback.load() avant d'utiliser le pipeline."
            )
        tfidf_answer, tfidf_score, _ = tfidf_search(question)
        logger.info(
            "[pipeline] TFIDF direct (faiss=%.4f, tfidf=%.4f) | '%s'",
            best_score, tfidf_score, question[:50],
        )
        return PipelineResult(
            answer=tfidf_answer, level="tfidf", score=best_score,
            latency_ms=_ms(t0), source="tfidf_cache",
            categorie=best.get("categorie", "") if best else "",
            method="tfidf_direct", contexts=contexts,
        )

    # Niveau 4 — LLM (score < SCORE_LLM)
    # Les top-3 contextes FAISS sont injectés dans le prompt même avec de faibles scores.
    ollama = check_availability()
    if not ollama["available"]:
        logger.warning(
            "[pipeline] OFFBASE — Ollama indisponible (score=%.4f) : %s",
            best_score, ollama["error"],
        )
        return PipelineResult(
            answer=(
                "Je n'ai pas cette information dans ma base de données SUP'PTIC. "
                "Pour plus de détails, contactez directement le secrétariat."
            ),
            level="offbase", score=best_score,
            latency_ms=_ms(t0), method="offbase",
        )

    prompt = build_prompt(question, contexts, history)
    logger.info("[pipeline] LLM (score=%.4f) | '%s'", best_score, question[:50])
    try:
        llm_answer = generate(prompt, level="llm")
    except Exception as exc:
        logger.error("[pipeline] LLM erreur : %s", exc)
        return PipelineResult(
            answer=(
                "Je n'ai pas cette information dans ma base de données SUP'PTIC. "
                "Pour plus de détails, contactez directement le secrétariat."
            ),
            level="offbase", score=best_score,
            latency_ms=_ms(t0), method="offbase_llm_error",
        )

    return PipelineResult(
        answer=llm_answer, level="llm", score=best_score,
        latency_ms=_ms(t0), source="ollama",
        categorie=best.get("categorie", "") if best else "",
        method="llm_phi3", contexts=contexts,
    )


# -------------------------------------------------------------------
# Pipeline streaming SSE
# -------------------------------------------------------------------
def ask_stream(
    question: str,
    history:  list[dict] | None = None,
) -> Iterator[str]:
    """
    Générateur SSE pour StreamingHttpResponse Django.

    Protocole émis :
        event: start\\ndata: <level>|<method>\\n\\n   — métadonnées
        data: <texte>\\n\\n                           — token(s) de réponse
        event: done\\ndata: <latency_ms>\\n\\n         — fin
        event: error\\ndata: <message>\\n\\n           — erreur système
    """
    t0 = time.time()
    question = question.strip()

    # --- Question vide ---
    if not question:
        yield build_sse_event("conv|empty", event="start")
        yield build_sse_event("Veuillez saisir une question.")
        yield build_sse_event(_ms(t0), event="done")
        return

    # --- Niveau 1 — CONV ---
    conv_answer = detect_conv(question)
    if conv_answer:
        logger.info("[stream] CONV '%s'", question[:50])
        yield build_sse_event("conv|regex", event="start")
        yield build_sse_event(conv_answer)
        yield build_sse_event(_ms(t0), event="done")
        return

    # --- Vectorisation + FAISS ---
    query_vec  = _get_vec(question)
    contexts   = search_with_metadata(query_vec, k=3)
    best       = contexts[0] if contexts else None
    best_score = best["score"] if best else 0.0
    logger.info("[stream] FAISS score=%.4f | '%s'", best_score, question[:50])

    # --- Niveau 2 — DIRECT ---
    if best and best_score >= SCORE_DIRECT:
        answer = best["response"].strip() or (
            "Information disponible mais réponse vide. Contactez le secrétariat."
        )
        logger.info("[stream] DIRECT (score=%.4f)", best_score)
        yield build_sse_event("direct|faiss_direct", event="start")
        yield build_sse_event(answer)
        yield build_sse_event(_ms(t0), event="done")
        return

    # --- Niveau 3 — TFIDF ---
    if best and best_score >= SCORE_LLM:
        if not tfidf_is_loaded():
            logger.error("[stream] ERREUR SYSTÈME : TF-IDF non chargé.")
            yield build_sse_event(
                "Pipeline mal initialisé : TF-IDF absent. Contactez l'administrateur.",
                event="error",
            )
            yield build_sse_event(_ms(t0), event="done")
            return
        tfidf_answer, tfidf_score, _ = tfidf_search(question)
        logger.info(
            "[stream] TFIDF direct (faiss=%.4f, tfidf=%.4f) | '%s'",
            best_score, tfidf_score, question[:50],
        )
        yield build_sse_event("tfidf|tfidf_direct", event="start")
        yield build_sse_event(tfidf_answer)
        yield build_sse_event(_ms(t0), event="done")
        return

    # --- Niveau 4 — LLM (score < SCORE_LLM) ---
    ollama = check_availability()
    if not ollama["available"]:
        logger.warning(
            "[stream] OFFBASE — Ollama indisponible (score=%.4f) : %s",
            best_score, ollama["error"],
        )
        yield build_sse_event("offbase|offbase", event="start")
        yield build_sse_event(
            "Je n'ai pas cette information dans ma base de données SUP'PTIC. "
            "Pour plus de détails, contactez directement le secrétariat."
        )
        yield build_sse_event(_ms(t0), event="done")
        return

    prompt = build_prompt(question, contexts, history)
    logger.info("[stream] LLM (score=%.4f) | '%s'", best_score, question[:50])
    yield build_sse_event("llm|llm_phi3", event="start")

    try:
        for token in generate_stream(prompt, level="llm"):
            yield build_sse_event(token)
    except Exception as exc:
        logger.error("[stream] LLM erreur streaming : %s", exc)
        yield build_sse_event(str(exc), event="error")

    yield build_sse_event(_ms(t0), event="done")


# -------------------------------------------------------------------
# Santé du pipeline
# -------------------------------------------------------------------
def health() -> dict:
    ollama = check_availability()
    return {
        "faiss_loaded":     faiss_is_loaded(),
        "faiss_stats":      get_index_stats(),
        "tfidf_loaded":     tfidf_is_loaded(),
        "tfidf_stats":      tfidf_stats(),
        "ollama_available": ollama["available"],
        "ollama_model":     ollama["model"],
        "ollama_error":     ollama["error"],
        "cache_size":       _cached_encode.cache_info().currsize,
        "ready":            faiss_is_loaded() and tfidf_is_loaded(),
    }


# -------------------------------------------------------------------
# Test rapide (python rag_pipeline.py)
# -------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    from faiss_search   import load_index
    from tfidf_fallback import load as tfidf_load

    print("=== Test rag_pipeline.py — Génération 3 (LLM réactivé) ===\n")
    load_index()
    tfidf_load()

    h = health()
    print(f"Health : faiss={h['faiss_loaded']} | tfidf={h['tfidf_loaded']} | ollama={h['ollama_available']}\n")

    test_cases = [
        ("Bonjour !",                        "conv"),
        ("Merci beaucoup",                   "conv"),
        ("C'est combien pour s'inscrire ?",  "direct"),
        ("Comment rejoindre le club info ?", "direct"),
        ("tarif scol",                       "tfidf"),
        ("Quel temps fait-il aujourd'hui ?", "llm"),    # score < 0.30 → LLM si Ollama dispo
    ]

    for question, expected in test_cases:
        result = ask(question)
        status = "OK" if result.level == expected else f"KO (attendu: {expected})"
        print(
            f"[{result.level.upper():7}] [{status}] {question}\n"
            f"  score={result.score:.4f} | {result.latency_ms:.0f}ms | {result.method}\n"
            f"  → {result.answer[:100]}\n"
        )

    print("=== Test ask_stream ===\n")
    for raw in ask_stream("Quel est le processus d'admission ?"):
        print(repr(raw))
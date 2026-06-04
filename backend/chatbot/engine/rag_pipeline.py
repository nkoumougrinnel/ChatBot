"""
rag_pipeline.py — Orchestrateur du pipeline RAG à 4 niveaux (Génération 3 — LLM réactivé).

Niveau 1 — CONV    : regex sur formules conversationnelles → réponse hardcodée   < 1 ms
Niveau 2 — DIRECT  : score FAISS >= 0.55 → réponse FAISS directe, sans LLM      ~150 ms
Niveau 3 — TFIDF   : 0.30 <= score < 0.55 → réponse TF-IDF directe, sans LLM   ~50 ms
Niveau 4 — LLM     : score < 0.30 → top-3 FAISS injectés dans le prompt Gemini  ~1-5 s
           OFFBASE  : score < 0.30 ET Gemini indisponible → refus propre          < 1 ms

Règle Gen3 :
  - Le LLM est appelé UNIQUEMENT quand FAISS ne trouve rien (score < SCORE_LLM).
  - Les top-3 résultats FAISS sont toujours passés en contexte, même avec de faibles scores.
  - Si Gemini est indisponible, le pipeline bascule proprement sur le refus OFFBASE.

Ce module est le seul point d'entrée appelé par views.py.
"""

from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass, field
from functools import lru_cache
from collections.abc import Iterator

import numpy as np

try:
    from .embedder       import encode
    from .faiss_search   import search_with_metadata, SCORE_DIRECT, SCORE_LLM, is_loaded as faiss_is_loaded, get_index_stats
    from .prompt_builder import detect_conv, build_prompt
    from .tfidf_fallback import is_loaded as tfidf_is_loaded, get_stats as tfidf_stats
    from .llm_client     import check_availability, generate, generate_stream
    from .coherence      import is_off_topic_query, resolve_kb_answer
except ImportError:
    from chatbot.engine.embedder       import encode
    from chatbot.engine.faiss_search   import search_with_metadata, SCORE_DIRECT, SCORE_LLM, is_loaded as faiss_is_loaded, get_index_stats
    from chatbot.engine.prompt_builder import detect_conv, build_prompt
    from chatbot.engine.tfidf_fallback import is_loaded as tfidf_is_loaded, get_stats as tfidf_stats
    from chatbot.engine.llm_client     import check_availability, generate, generate_stream
    from chatbot.engine.coherence      import is_off_topic_query, resolve_kb_answer

logger = logging.getLogger(__name__)

# Seuils de cohérence question ↔ réponse (surchargeables via .env)
TFIDF_ANSWER_MIN = float(os.environ.get("TFIDF_ANSWER_MIN", "0.38"))
FAISS_MEDIUM_MIN = float(os.environ.get("FAISS_MEDIUM_MIN", "0.45"))
LLM_CONTEXT_MIN = float(os.environ.get("LLM_CONTEXT_MIN", "0.22"))
OVERLAP_MIN_DIRECT = float(os.environ.get("OVERLAP_MIN_DIRECT", "0.18"))
SCORE_DIRECT_OVERRIDE = float(os.environ.get("SCORE_DIRECT_OVERRIDE", "0.88"))

_STOPWORDS = frozenset({
    "les", "des", "une", "un", "est", "sont", "dans", "pour", "par", "sur",
    "avec", "sans", "plus", "tout", "tous", "toute", "comment", "quel", "quels",
    "quelle", "quelles", "que", "qui", "où", "ou", "et", "the", "you", "your",
    "peut", "puis", "faire", "être", "avoir", "chez", "aux", "du", "de", "la",
    "le", "ce", "cette", "ces", "mon", "mes", "son", "ses", "notre", "votre",
})

_OFFBASE_MSG = (
    "Je n'ai pas cette information dans ma base de données SUP'PTIC. "
    "Pour plus de détails, contactez directement le secrétariat."
)


def _tfidf_acceptable(tfidf_score: float, tfidf_answer: str) -> bool:
    return (
        tfidf_score >= TFIDF_ANSWER_MIN
        and bool(tfidf_answer.strip())
        and not tfidf_answer.startswith("Je n'ai pas")
    )


def _faiss_medium_acceptable(faiss_score: float, faiss_answer: str) -> bool:
    return (
        faiss_score >= FAISS_MEDIUM_MIN
        and len(faiss_answer.strip()) >= 60
    )


def _tokens(text: str) -> set[str]:
    return {
        w
        for w in re.findall(r"[a-zàâäçéèêëîïôùûüœ']{3,}", (text or "").lower())
        if w not in _STOPWORDS
    }


def _context_reference(ctx: dict | None) -> str:
    if not ctx:
        return ""
    return " ".join(
        str(ctx.get(k, "") or "")
        for k in ("example", "response", "intent", "categorie")
    )


def _context_overlap(question: str, ctx: dict | None) -> float:
    q = _tokens(question)
    if not q:
        return 1.0
    ref = _tokens(_context_reference(ctx))
    if not ref:
        return 0.0
    return len(q & ref) / len(q)


def _critical_terms_ok(question: str, ctx: dict | None) -> bool:
    """Mots-clés métier de la question doivent apparaître dans le contexte FAISS."""
    q = question.lower()
    ref = _context_reference(ctx).lower()
    rules: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
        (("inscri", "inscription", "candidat"), ("inscri", "inscription", "candidat", "admission")),
        (("frais", "scolar", "tarif", "payer", "paiement"), ("frais", "scolar", "tarif", "paiement", "coût", "cout")),
        (("stage", "stages"), ("stage", "stages", "alternance")),
        (("examen", "concours"), ("examen", "concours", "épreuve", "epreuve")),
        (("filière", "filiere", "filières", "formations"), ("filière", "filiere", "formation", "cycle", "licence", "master", "filières")),
        (("campus", "adresse", "trouve", "localis"), ("campus", "adresse", "yaound", "elig", "situ")),
        (("capitale", "france", "paris", "monde"), ()),  # hors périmètre SUP'PTIC
    ]
    for triggers, required in rules:
        if any(t in q for t in triggers):
            if not required:
                return False
            return any(r in ref for r in required)
    return True


def _faiss_direct_allowed(question: str, ctx: dict | None, score: float) -> bool:
    if score >= SCORE_DIRECT_OVERRIDE:
        return True
    if not _critical_terms_ok(question, ctx):
        return False
    return _context_overlap(question, ctx) >= OVERLAP_MIN_DIRECT


def _faq_id_from_ref_question(ref_q: str) -> int | None:
    if not ref_q:
        return None
    try:
        from faq.models import FAQ
    except ImportError:
        return None
    ref = ref_q.strip()
    faq = FAQ.objects.filter(is_active=True, question__iexact=ref).only("id").first()
    if faq:
        return faq.id
    faq = FAQ.objects.filter(is_active=True, question__icontains=ref[:80]).only("id").first()
    return faq.id if faq else None


def _pipeline_result_from_pick(pick: dict, best: dict | None, contexts: list, t0: float) -> PipelineResult:
    return PipelineResult(
        answer=pick["answer"],
        level=pick["level"],
        score=pick["score"],
        latency_ms=_ms(t0),
        source="tfidf_cache" if pick["method"] == "tfidf_direct" else (best or {}).get("source", ""),
        categorie=(best or {}).get("categorie", ""),
        method=pick["method"],
        faq_id=_faq_id_from_ref_question(pick.get("ref_q", "")),
        contexts=contexts,
    )


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
    faq_id:     int | None = None
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

    if is_off_topic_query(question):
        logger.info("[pipeline] OFFBASE — hors périmètre | '%s'", question[:50])
        return PipelineResult(
            answer=_OFFBASE_MSG, level="offbase", score=0.0,
            latency_ms=_ms(t0), method="off_topic",
        )

    # Vectorisation + FAISS
    query_vec  = _get_vec(question)
    contexts   = search_with_metadata(query_vec, k=3)
    best       = contexts[0] if contexts else None
    best_score = best["score"] if best else 0.0
    logger.info("[pipeline] FAISS score=%.4f | '%s'", best_score, question[:50])

    # Niveaux 2–3 — base de connaissances (FAISS + TF-IDF, sélection cohérente)
    if best and best_score >= SCORE_LLM:
        if not tfidf_is_loaded():
            logger.error("[pipeline] ERREUR SYSTÈME : TF-IDF non chargé.")
            raise RuntimeError(
                "Pipeline Gen3 mal initialisé : TF-IDF non chargé. "
                "Appelez tfidf_fallback.load() avant d'utiliser le pipeline."
            )
        pick = resolve_kb_answer(question, contexts, tfidf_answer_min=TFIDF_ANSWER_MIN)
        if pick:
            logger.info(
                "[pipeline] KB %s score=%.4f overlap=%.2f | '%s'",
                pick["method"], pick["score"], pick["overlap"], question[:50],
            )
            return _pipeline_result_from_pick(pick, best, contexts, t0)
        logger.info("[pipeline] Pas de réponse cohérente (faiss=%.4f)", best_score)
        return PipelineResult(
            answer=_OFFBASE_MSG, level="offbase", score=best_score,
            latency_ms=_ms(t0), method="low_confidence",
        )

    # Niveau 4 — LLM (score FAISS < SCORE_LLM)
    # Les top-3 contextes FAISS sont injectés dans le prompt même avec de faibles scores.
    llm = check_availability()
    if not llm["available"]:
        logger.warning(
            "[pipeline] OFFBASE — LLM Gemini indisponible (score=%.4f) : %s",
            best_score, llm["error"],
        )
        return PipelineResult(
            answer=_OFFBASE_MSG, level="offbase", score=best_score,
            latency_ms=_ms(t0), method="offbase",
        )

    if best_score < LLM_CONTEXT_MIN:
        logger.info("[pipeline] OFFBASE — contexte trop faible (score=%.4f)", best_score)
        return PipelineResult(
            answer=_OFFBASE_MSG, level="offbase", score=best_score,
            latency_ms=_ms(t0), method="low_context",
        )

    prompt = build_prompt(question, contexts, history)
    logger.info("[pipeline] LLM (score=%.4f) | '%s'", best_score, question[:50])
    try:
        llm_answer = generate(prompt, level="llm")
    except Exception as exc:
        logger.error("[pipeline] LLM erreur : %s", exc)
        return PipelineResult(
            answer=_OFFBASE_MSG, level="offbase", score=best_score,
            latency_ms=_ms(t0), method="offbase_llm_error",
        )

    return PipelineResult(
        answer=llm_answer, level="llm", score=best_score,
        latency_ms=_ms(t0), source="gemini",
        categorie=best.get("categorie", "") if best else "",
        method="llm_gemini", contexts=contexts,
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

    if is_off_topic_query(question):
        logger.info("[stream] OFFBASE — hors périmètre | '%s'", question[:50])
        yield build_sse_event("offbase|off_topic", event="start")
        yield build_sse_event(_OFFBASE_MSG)
        yield build_sse_event(_ms(t0), event="done")
        return

    # --- Vectorisation + FAISS ---
    query_vec  = _get_vec(question)
    contexts   = search_with_metadata(query_vec, k=3)
    best       = contexts[0] if contexts else None
    best_score = best["score"] if best else 0.0
    logger.info("[stream] FAISS score=%.4f | '%s'", best_score, question[:50])

    # --- Niveaux 2–3 — base de connaissances ---
    if best and best_score >= SCORE_LLM:
        if not tfidf_is_loaded():
            logger.error("[stream] ERREUR SYSTÈME : TF-IDF non chargé.")
            yield build_sse_event(
                "Pipeline mal initialisé : TF-IDF absent. Contactez l'administrateur.",
                event="error",
            )
            yield build_sse_event(_ms(t0), event="done")
            return
        pick = resolve_kb_answer(question, contexts, tfidf_answer_min=TFIDF_ANSWER_MIN)
        if pick:
            logger.info(
                "[stream] KB %s score=%.4f overlap=%.2f",
                pick["method"], pick["score"], pick["overlap"],
            )
            yield build_sse_event(f"{pick['level']}|{pick['method']}", event="start")
            yield build_sse_event(pick["answer"])
            yield build_sse_event(_ms(t0), event="done")
            return
        logger.info("[stream] Pas de réponse cohérente (faiss=%.4f)", best_score)
        yield build_sse_event("offbase|low_confidence", event="start")
        yield build_sse_event(_OFFBASE_MSG)
        yield build_sse_event(_ms(t0), event="done")
        return

    # --- Niveau 4 — LLM (score FAISS < SCORE_LLM) ---
    llm = check_availability()
    if not llm["available"]:
        logger.warning(
            "[stream] OFFBASE — LLM Gemini indisponible (score=%.4f) : %s",
            best_score, llm["error"],
        )
        yield build_sse_event("offbase|offbase", event="start")
        yield build_sse_event(_OFFBASE_MSG)
        yield build_sse_event(_ms(t0), event="done")
        return

    if best_score < LLM_CONTEXT_MIN:
        logger.info("[stream] OFFBASE — contexte trop faible (score=%.4f)", best_score)
        yield build_sse_event("offbase|low_context", event="start")
        yield build_sse_event(_OFFBASE_MSG)
        yield build_sse_event(_ms(t0), event="done")
        return

    prompt = build_prompt(question, contexts, history)
    logger.info("[stream] LLM (score=%.4f) | '%s'", best_score, question[:50])
    yield build_sse_event("llm|llm_gemini", event="start")

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
    llm = check_availability()
    return {
        "faiss_loaded":  faiss_is_loaded(),
        "faiss_stats":   get_index_stats(),
        "tfidf_loaded":  tfidf_is_loaded(),
        "tfidf_stats":   tfidf_stats(),
        "llm_available": llm["available"],
        "llm_model":     llm["model"],
        "llm_error":     llm["error"],
        "cache_size":    _cached_encode.cache_info().currsize,
        "ready":         faiss_is_loaded() and tfidf_is_loaded(),
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
    print(f"Health : faiss={h['faiss_loaded']} | tfidf={h['tfidf_loaded']} | llm={h['llm_available']}\n")

    test_cases = [
        ("Bonjour !",                        "conv"),
        ("Merci beaucoup",                   "conv"),
        ("C'est combien pour s'inscrire ?",  "direct"),
        ("Comment rejoindre le club info ?", "direct"),
        ("tarif scol",                       "tfidf"),
        ("Quel temps fait-il aujourd'hui ?", "llm"),    # score < 0.30 → LLM si Gemini dispo
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
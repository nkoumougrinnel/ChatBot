"""
Sélection cohérente question ↔ réponse (FAISS + TF-IDF + filtres hors-sujet).
"""
from __future__ import annotations

import re
import unicodedata

from .faiss_search import SCORE_DIRECT, SCORE_LLM

# Importés depuis rag_pipeline via paramètres ou os.environ côté appelant
TFIDF_ANSWER_MIN = 0.38

_STOP = frozenset({
    "le", "la", "les", "de", "du", "des", "a", "au", "aux", "un", "une",
    "et", "ou", "en", "sur", "pour", "par", "comment", "quels", "quelles",
    "que", "qui", "est", "sont", "je", "tu", "vous", "mon", "ma", "mes",
    "the", "is", "are", "what", "where", "how",
})

_JOKE_MARKERS = (
    "bluffer",
    "poker",
    "pourquoi les développeurs",
    "pourquoi les robots",
    "mode sombre",
)

_OFF_TOPIC_PATTERNS = (
    re.compile(r"\bcapitale\s+(de\s+la\s+)?france\b", re.I),
    re.compile(r"\bquelle\s+est\s+la\s+capitale\b", re.I),
    re.compile(r"\b(météo|weather|température)\b", re.I),
    re.compile(r"\b(recette|météo)\s+de\b", re.I),
    re.compile(r"\b(president|président)\s+(des\s+)?usa\b", re.I),
    re.compile(r"\bbitcoin\b", re.I),
)


def _normalize_tokens(text: str) -> set[str]:
    text = unicodedata.normalize("NFKD", (text or "").lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    words = re.findall(r"[a-z0-9']+", text)
    return {w for w in words if len(w) > 2 and w not in _STOP}


def lexical_overlap(user_question: str, reference_question: str) -> float:
    """Part des mots significatifs de la question utilisateur présents dans la référence."""
    u = _normalize_tokens(user_question)
    r = _normalize_tokens(reference_question)
    if not u:
        return 0.0
    return len(u & r) / len(u)


def is_off_topic_query(question: str) -> bool:
    return any(p.search(question) for p in _OFF_TOPIC_PATTERNS)


_DOMAIN_RULES: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
    (("inscri", "inscription", "candidat"), ("inscri", "inscription", "admission", "candidat")),
    (("frais", "scolar", "tarif", "payer", "paiement"), ("frais", "scolar", "tarif", "paiement", "coût", "cout")),
    (("stage", "stages"), ("stage", "stages", "alternance")),
    (("examen", "concours"), ("examen", "concours", "épreuve", "epreuve")),
    (("filière", "filiere", "filières"), ("filière", "filiere", "filières", "formation", "cycle", "licence", "master")),
    (("campus", "adresse", "trouve", "localis", "où"), ("campus", "adresse", "yaound", "elig", "situ", "trouve", "localis")),
    (("club", "informatique"), ("club", "informatique", "association")),
    (("horaire", "ouverture", "heure"), ("horaire", "ouverture", "heure", "8h", "17h", "lundi")),
]


def domain_terms_match(user_question: str, reference_question: str) -> bool:
    """La question de référence doit couvrir le sujet demandé par l'utilisateur."""
    u = user_question.lower()
    r = reference_question.lower()
    matched_rule = False
    for triggers, required in _DOMAIN_RULES:
        if any(t in u for t in triggers):
            matched_rule = True
            if not any(req in r for req in required):
                return False

    # Inscription générale : éviter les réponses « événements culturels » hors sujet
    if any(t in u for t in ("inscri", "inscription")) and not any(
        t in u for t in ("culturel", "événement", "evenement", "club")
    ):
        if any(t in r for t in ("culturel", "événement", "evenement")):
            if not any(t in r for t in ("formation", "admission", "candidat", "programme", "scolar")):
                return False

    return True


def is_joke_answer(answer: str, user_question: str) -> bool:
    if "blague" in user_question.lower():
        return False
    low = (answer or "").lower()
    return any(m in low for m in _JOKE_MARKERS)


def resolve_kb_answer(
    question: str,
    contexts: list[dict],
    *,
    tfidf_answer_min: float = TFIDF_ANSWER_MIN,
) -> dict | None:
    """
    Fusionne FAISS (top contexts) et TF-IDF pour choisir la réponse la plus alignée
    lexicalement avec la question utilisateur.

    Returns dict: answer, score, method, level, ref_question — ou None.
    """
    from .tfidf_fallback import search_top_k

    candidates: list[dict] = []

    for ctx in contexts[:3]:
        score = float(ctx.get("score", 0))
        if score < SCORE_LLM:
            continue
        ref = (ctx.get("example") or ctx.get("question") or "").strip()
        ans = (ctx.get("response") or "").strip()
        if not ans:
            continue
        if not domain_terms_match(question, ref):
            continue
        overlap = lexical_overlap(question, ref)
        candidates.append({
            "score": score,
            "answer": ans,
            "ref_q": ref,
            "method": "faiss_direct",
            "overlap": overlap,
            "rank": overlap * 0.72 + score * 0.28,
        })

    for hit in search_top_k(question, k=3):
        score = float(hit.get("score", 0))
        if score < tfidf_answer_min:
            continue
        ans = (hit.get("answer") or "").strip()
        if not ans or ans.startswith("Je n'ai pas"):
            continue
        ref = (hit.get("question") or "").strip()
        if not domain_terms_match(question, ref):
            continue
        overlap = lexical_overlap(question, ref)
        candidates.append({
            "score": score,
            "answer": ans,
            "ref_q": ref,
            "method": "tfidf_direct",
            "overlap": overlap,
            "rank": overlap * 0.72 + score * 0.28,
        })

    if not candidates:
        return None

    candidates.sort(key=lambda c: c["rank"], reverse=True)

    for pick in candidates:
        if is_joke_answer(pick["answer"], question):
            continue
        if not domain_terms_match(question, pick.get("ref_q", "")):
            continue
        if pick["overlap"] < 0.20 and pick["score"] < 0.72:
            continue
        if pick["overlap"] < 0.25 and pick["score"] < 0.50:
            continue
        level = "direct" if pick["score"] >= SCORE_DIRECT else "tfidf"
        pick["level"] = level
        return pick

    return None

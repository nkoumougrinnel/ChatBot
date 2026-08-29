"""
prompt_builder.py — Construction des prompts pour le LLM (Gemini).
Version optimisée : renforce les instructions anti-hallucination.
"""

from __future__ import annotations

import re

# -------------------------------------------------------------------
# Message système — renforcé contre les hallucinations
# -------------------------------------------------------------------
_SYSTEM_MESSAGE = (
    "Tu es SUP'ONE, l'assistant officiel de SUP'PTIC, "
    "l'École Supérieure des Postes et Télécommunications du Cameroun.\n\n"
    "RÈGLES ABSOLUES (jamais enfreintes) :\n"
    "1. Tu réponds UNIQUEMENT en français.\n"
    "2. Tu te bases EXCLUSIVEMENT sur le [CONTEXTE] fourni ci-dessous.\n"
    "3. SI l'information n'est PAS dans le [CONTEXTE], tu réponds EXACTEMENT : "
    "\"Je n'ai pas cette information dans ma base de données SUP'PTIC. "
    "Pour plus de détails, contactez directement le secrétariat.\"\n"
    "4. Tu ne fabriques JAMAIS d'information. Pas d'invention, pas de supposition, pas d'improvisation.\n"
    "5. Tes réponses sont courtes : 1 à 3 phrases maximum.\n"
    "6. Tu ne donnes JAMAIS de conseils médicaux, juridiques, financiers ou personnels.\n"
    "7. Tu ne réponds qu'aux questions en rapport avec SUP'PTIC (admissions, filières, "
    "examens, vie étudiante, services, infrastructure).\n"
    "8. Si la question est hors sujet, tu réponds : "
    "\"Cette question ne concerne pas SUP'PTIC. Je suis spécialisé dans les informations "
    "de l'école. Posez-moi une question sur les admissions, les filières ou les services.\"\n"
    "9. Tu ne répètes JAMAIS la question de l'utilisateur dans ta réponse.\n"
    "10. Tu n'utilises JAMAIS de formules comme \"D'après mes informations\" ou \"Il semble que\"."
)

# -------------------------------------------------------------------
# Niveau 1 — CONV : réponses hardcodées (< 1 ms, aucun modèle appelé)
# -------------------------------------------------------------------
_CONV_RESPONSES: dict[str, str] = {
    "bonjour":   "Bonjour ! Je suis SUP'ONE, l'assistant du Club Informatique de SUP'PTIC. Comment puis-je vous aider ?",
    "salut":     "Salut ! Je suis SUP'ONE. Posez-moi votre question sur SUP'PTIC.",
    "merci":     "Avec plaisir ! N'hésitez pas si vous avez d'autres questions.",
    "au revoir": "Au revoir ! Bonne continuation à SUP'PTIC.",
    "qui es-tu": "Je suis SUP'ONE, le chatbot du Club Informatique de SUP'PTIC.",
    "aide":      "Je peux vous renseigner sur les frais, les filières, les inscriptions et les services de SUP'PTIC.",
}

_CONV_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(bonjour|bonsoir|hello|hi)\b", re.I),            "bonjour"),
    (re.compile(r"\b(salut)\b", re.I),                                "salut"),
    (re.compile(r"\b(merci|thank|thx)\b", re.I),                     "merci"),
    (re.compile(r"\b(au revoir|bye|ciao|adieu)\b", re.I),            "au revoir"),
    (re.compile(r"\b(qui es[- ]tu|ton nom|tu t.appelles)\b", re.I),  "qui es-tu"),
    (re.compile(r"^\s*(aide|help|\?)\s*$", re.I),                     "aide"),
]


def detect_conv(text: str) -> str | None:
    """
    Niveau 1 — Détecte les formules conversationnelles par regex.
    """
    for pattern, key in _CONV_PATTERNS:
        if pattern.search(text):
            return _CONV_RESPONSES[key]
    return None


# -------------------------------------------------------------------
# Niveau 2 — DIRECT : prompt minimal pour reformulation (debug)
# -------------------------------------------------------------------
def build_direct_prompt(question: str, best_context: dict) -> str:
    response_text = best_context.get("response", "").strip()
    categorie     = best_context.get("categorie", "")
    return (
        f"<|system|>\n{_SYSTEM_MESSAGE}<|end|>\n"
        f"<|user|>\n"
        f"[CONTEXTE — {categorie}]\n{response_text}\n\n"
        f"Reformule en 1 à 2 phrases claires :\n"
        f"{question.strip()}<|end|>\n"
        f"<|assistant|>\n"
    )


# -------------------------------------------------------------------
# Niveau 3 — LLM : prompt complet avec contexte FAISS + historique
# -------------------------------------------------------------------
def build_prompt(
    question: str,
    contexts: list[dict],
    history:  list[dict] | None = None,
    max_contexts: int = 3,
) -> str:
    """
    Prompt complet pour le LLM avec contexte FAISS et historique.
    Optimisé pour réduire les hallucinations.
    """
    body = _build_user_body(history, contexts[:max_contexts], question)
    return (
        f"<|system|>\n{_SYSTEM_MESSAGE}<|end|>\n"
        f"<|user|>\n{body}<|end|>\n"
        f"<|assistant|>\n"
    )


def _build_user_body(
    history:  list[dict] | None,
    contexts: list[dict],
    question: str,
) -> str:
    """Corps du message utilisateur : historique + contexte + question."""
    parts: list[str] = []

    # Historique : max 2 derniers échanges, tronqués à 150 chars
    if history:
        parts.append("[HISTORIQUE]")
        for turn in history[-2:]:
            label   = "Étudiant" if turn.get("role") == "user" else "Assistant"
            content = turn.get("content", "").strip()[:150]
            parts.append(f"{label} : {content}")
        parts.append("")

    # Contexte FAISS
    if contexts:
        parts.append("[CONTEXTE — Sources fiables SUP'PTIC]")
        for i, ctx in enumerate(contexts, 1):
            cat  = ctx.get("categorie", "Général")
            src  = ctx.get("source", "")
            text = ctx.get("response", "").strip()
            # Tronquer les contextes trop longs pour éviter la confusion
            if len(text) > 400:
                text = text[:400] + "…"
            src_tag = f" | {src}" if src else ""
            parts.append(f"[{i}] {cat}{src_tag}\n{text}")
        parts.append("")
    else:
        parts.append("[CONTEXTE]\n(Aucune information disponible dans la base SUP'PTIC.)\n")

    parts.append(f"Question : {question.strip()}")
    parts.append(
        "IMPORTANT : Réponds UNIQUEMENT à partir du [CONTEXTE]. "
        "Si l'information n'y est pas, dis-le clairement. "
        "Ne fabrique AUCUNE information. Sois concis (1-3 phrases max)."
    )
    return "\n".join(parts) + "\n"


# -------------------------------------------------------------------
# Test rapide (python prompt_builder.py)
# -------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Test prompt_builder.py — Version optimisée ===\n")

    tests_conv = ["Bonjour !", "Merci beaucoup", "Qui es-tu ?", "Quel temps ?"]
    for q in tests_conv:
        r = detect_conv(q)
        print(f"CONV '{q}' → {r}\n")

    ctx = {"categorie": "Admissions", "source": "e-supptic.cm",
           "response": "Les frais de scolarité à SUP'PTIC s'élèvent à 500 000 FCFA par an."}
    p = build_direct_prompt("C'est combien pour s'inscrire ?", ctx)
    print(f"--- Prompt DIRECT ---\n{p}")

    contexts = [
        {"categorie": "Admissions", "source": "brochure_2025.pdf",
         "response": "Le paiement peut être effectué en deux tranches."},
    ]
    history = [
        {"role": "user",      "content": "Quelles sont les filières ?"},
        {"role": "assistant", "content": "SUP'PTIC propose Réseaux, Télécoms et Informatique."},
    ]
    p2 = build_prompt("C'est combien ?", contexts, history)
    print(f"--- Prompt LLM ---\n{p2}")

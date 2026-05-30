"""
prompt_builder.py — Construction des prompts pour Phi-3 Mini.
Génération 3 : prompts différenciés par niveau, detect_conv() pour le pipeline.

Fonctions publiques utilisées par rag_pipeline.py :
    detect_conv(text)                       → str | None   (Niveau 1)
    build_prompt(question, contexts, history) → str         (debug LLM uniquement)
    build_direct_prompt(question, context)  → str          (debug LLM uniquement)

Note : en Gen3, le LLM n'est plus appelé par le pipeline principal.
build_prompt et build_direct_prompt restent disponibles pour les tests via
views.test_llm_latency() et les scripts de debug.
"""

from __future__ import annotations

import re

# -------------------------------------------------------------------
# Message système — commun à tous les niveaux LLM
# -------------------------------------------------------------------
_SYSTEM_MESSAGE = (
    "Tu es SUP'ONE, l'assistant officiel de SUP'PTIC, "
    "l'École Supérieure des Postes et Télécommunications du Cameroun.\n\n"
    "RÈGLES :\n"
    "1. Tu réponds UNIQUEMENT en français.\n"
    "2. Tu te bases EXCLUSIVEMENT sur le [CONTEXTE] fourni.\n"
    "3. Si l'information n'est PAS dans le [CONTEXTE], réponds EXACTEMENT : "
    "\"Je n'ai pas cette information dans ma base. Contactez le secrétariat de SUP'PTIC.\"\n"
    "4. Tu ne fabriques AUCUNE information.\n"
    "5. Tes réponses sont courtes : 2 à 3 phrases maximum."
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
    Appelé en premier par rag_pipeline.ask() et ask_stream().

    Returns:
        Réponse hardcodée si match, None sinon.
    """
    for pattern, key in _CONV_PATTERNS:
        if pattern.search(text):
            return _CONV_RESPONSES[key]
    return None


# -------------------------------------------------------------------
# Niveau 2 — DIRECT : prompt minimal pour reformulation (debug)
# -------------------------------------------------------------------
def build_direct_prompt(question: str, best_context: dict) -> str:
    """
    Prompt allégé pour reformuler une réponse FAISS directe.
    Utilisé uniquement en debug — en Gen3, le Niveau 2 retourne la
    réponse stockée sans passer par le LLM.
    """
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
# Niveau 3 — LLM : prompt complet avec contexte FAISS + historique (debug)
# -------------------------------------------------------------------
def build_prompt(
    question: str,
    contexts: list[dict],
    history:  list[dict] | None = None,
    max_contexts: int = 3,
) -> str:
    """
    Prompt complet pour le LLM avec contexte FAISS et historique.
    Utilisé uniquement en debug via views.test_llm_latency().
    En Gen3, le pipeline n'atteint jamais ce niveau.

    Args:
        question:     Question de l'étudiant.
        contexts:     Résultats de faiss_search.search_with_metadata().
        history:      Derniers échanges [{role, content}] (max 2 retenus).
        max_contexts: Nombre max de blocs de contexte (défaut 3).
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

    # Historique : max 2 derniers échanges, tronqués à 200 chars
    if history:
        parts.append("[HISTORIQUE]")
        for turn in history[-2:]:
            label   = "Étudiant" if turn.get("role") == "user" else "Assistant"
            content = turn.get("content", "").strip()[:200]
            parts.append(f"{label} : {content}")
        parts.append("")

    # Contexte FAISS
    if contexts:
        parts.append("[CONTEXTE]")
        for i, ctx in enumerate(contexts, 1):
            cat  = ctx.get("categorie", "Général")
            src  = ctx.get("source", "")
            text = ctx.get("response", "").strip()
            src_tag = f" | {src}" if src else ""
            parts.append(f"[{i}] {cat}{src_tag}\n{text}")
        parts.append("")
    else:
        parts.append("[CONTEXTE]\n(Aucune information disponible.)\n")

    parts.append(f"Question : {question.strip()}")
    parts.append("Réponds uniquement à partir du [CONTEXTE], en français, de façon concise.")
    return "\n".join(parts) + "\n"


# -------------------------------------------------------------------
# Test rapide (python prompt_builder.py)
# -------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Test prompt_builder.py — Génération 3 ===\n")

    # Niveau 1 — CONV
    tests_conv = ["Bonjour !", "Merci beaucoup", "Qui es-tu ?", "Quel temps ?"]
    for q in tests_conv:
        r = detect_conv(q)
        print(f"CONV '{q}' → {r}\n")

    # Niveau 2 — DIRECT (debug)
    ctx = {"categorie": "Admissions", "source": "e-supptic.cm",
           "response": "Les frais de scolarité s'élèvent à 500 000 FCFA par an."}
    p = build_direct_prompt("C'est combien pour s'inscrire ?", ctx)
    print(f"--- Prompt DIRECT ---\n{p}")

    # Niveau 3 — LLM complet (debug)
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

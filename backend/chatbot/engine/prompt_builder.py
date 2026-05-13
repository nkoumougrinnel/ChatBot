"""
prompt_builder.py — Construction du prompt envoyé à Phi-3 Mini.

Assemble :
    - Le rôle système (instructions)
    - L'historique de conversation (optionnel)
    - Les contextes FAISS (top-k résultats)
    - La question de l'étudiant

Format respectant le template Phi-3 : <|system|>...<|user|>...<|assistant|>
"""

from __future__ import annotations

# -------------------------------------------------------------------
# Message système : instructions fixes pour le LLM
# -------------------------------------------------------------------
_SYSTEM_MESSAGE = (
    "Tu es SUP'ONE, l'assistant intelligent du Club Informatique de SUP'PTIC "
    "(Institut Supérieur des Postes et Télécommunications du Cameroun). "
    "Tu réponds UNIQUEMENT en français. "
    "Tu te bases EXCLUSIVEMENT sur les informations fournies dans le contexte ci-dessous. "
    "Si la réponse n'est pas dans le contexte, réponds : "
    "\"Je n'ai pas cette information dans ma base. Pour plus de détails, "
    "contactez le secrétariat de SUP'PTIC.\" "
    "Ne fabrique jamais d'informations non présentes dans le contexte."
)


def build_prompt(
    question: str,
    contexts: list[dict],
    history: list[dict] | None = None,
) -> str:
    """
    Construit le prompt complet à envoyer à Phi-3 Mini.

    Args:
        question: La question posée par l'étudiant (str).
        contexts: Liste de dicts retournés par faiss_search.search_with_metadata().
                  Chaque dict contient au moins : response, categorie, source, score.
        history:  Liste optionnelle des derniers échanges.
                  Format : [{"role": "user"|"assistant", "content": "..."}]
                  Maximum 3 échanges pour ne pas dépasser la fenêtre de contexte.

    Returns:
        Prompt complet formaté pour Phi-3 Mini (str).
    """
    # --- Assemblage final au format Phi-3 ---
    # CORRECTION : suppression de la variable `user_turn` (code mort) qui contenait
    # l'expression `chr(10).join(sections[1:])` écrite en texte brut dans une f-string
    # au lieu d'être évaluée. Le corps utilisateur est délégué à _build_user_body().
    prompt = (
        f"<|system|>\n{_SYSTEM_MESSAGE}<|end|>\n"
        f"<|user|>\n"
        f"{_build_user_body(history, contexts, question)}"
        f"<|end|>\n"
        f"<|assistant|>\n"
    )
    return prompt


def _build_user_body(
    history: list[dict] | None,
    contexts: list[dict],
    question: str,
) -> str:
    """Construit le corps du message utilisateur (historique + contexte + question)."""
    parts = []

    # Historique
    if history:
        recent = history[-3:]
        parts.append("[Historique de la conversation]")
        for turn in recent:
            role_label = "Étudiant" if turn.get("role") == "user" else "Assistant"
            parts.append(f"{role_label} : {turn.get('content', '').strip()}")
        parts.append("")  # ligne vide

    # Contexte FAISS
    if contexts:
        parts.append("[Informations disponibles sur SUP'PTIC]")
        for i, ctx in enumerate(contexts, start=1):
            score = ctx.get("score", 0.0)
            categorie = ctx.get("categorie", "Général")
            source = ctx.get("source", "")
            response_text = ctx.get("response", "").strip()
            source_info = f" | Source : {source}" if source else ""
            parts.append(
                f"--- Information {i} [{categorie}{source_info}] "
                f"(pertinence : {score:.2f}) ---\n{response_text}"
            )
        parts.append("")  # ligne vide
    else:
        parts.append("[Aucune information contextuelle disponible]\n")

    # Question
    parts.append(f"Question de l'étudiant : {question.strip()}")
    parts.append("Réponds uniquement à partir des informations fournies ci-dessus.")

    return "\n".join(parts) + "\n"


def build_no_context_prompt(question: str) -> str:
    """
    Prompt de fallback quand aucun contexte n'est disponible.
    Le LLM doit indiquer qu'il ne peut pas répondre.
    """
    prompt = (
        f"<|system|>\n{_SYSTEM_MESSAGE}<|end|>\n"
        f"<|user|>\n"
        f"[Aucune information contextuelle disponible]\n\n"
        f"Question de l'étudiant : {question.strip()}\n"
        f"Réponds uniquement à partir des informations fournies ci-dessus.<|end|>\n"
        f"<|assistant|>\n"
    )
    return prompt


# -------------------------------------------------------------------
# Test rapide (exécutable directement : python prompt_builder.py)
# -------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Test prompt_builder.py ===\n")

    sample_contexts = [
        {
            "score": 0.91,
            "categorie": "Admissions",
            "source": "e-supptic.cm",
            "response": "Les frais de scolarité à SUP'PTIC s'élèvent à 500 000 FCFA par an. "
                        "Ce montant couvre l'ensemble de la formation. "
                        "Des facilités de paiement peuvent être demandées au secrétariat.",
        },
        {
            "score": 0.72,
            "categorie": "Admissions",
            "source": "brochure_2025.pdf",
            "response": "Le paiement peut être effectué en deux tranches. "
                        "La première tranche est due au moment de l'inscription.",
        },
    ]

    sample_history = [
        {"role": "user", "content": "Quelles sont les filières disponibles ?"},
        {"role": "assistant", "content": "SUP'PTIC propose des filières en Réseaux, Télécoms et Informatique."},
    ]

    # Test avec historique
    prompt = build_prompt(
        question="C'est combien pour s'inscrire ?",
        contexts=sample_contexts,
        history=sample_history,
    )
    print("--- Prompt avec historique ---")
    print(prompt)
    print(f"\nLongueur du prompt : {len(prompt)} caractères")

    # Test sans contexte
    print("\n--- Prompt sans contexte ---")
    prompt_no_ctx = build_no_context_prompt("Quel temps fait-il ?")
    print(prompt_no_ctx)
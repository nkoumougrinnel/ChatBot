"""
prompt_builder.py — Construction des prompts pour Phi-3 Mini.
RAG à 3 niveaux : CONV → DIRECT → LLM
"""

# Message système constant
_SYSTEM_MESSAGE = (
    "Tu es SUP'ONE, l'assistant officiel de SUP'PTIC, "
    "l'École Supérieure des Postes et Télécommunications du Cameroun.\n\n"
    "RÈGLES :\n"
    "1. Tu réponds UNIQUEMENT en français.\n"
    "2. Tu te bases EXCLUSIVEMENT sur le [Contexte] fourni.\n"
    "3. Si l'information n'est PAS dans le [Contexte], réponds EXACTEMENT: "
    "\"Je n'ai pas cette information dans ma base. Contactez le secrétariat de SUP'PTIC.\"\n"
    "4. Tu ne fabriques AUCUNE information.\n"
    "5. Tes réponses sont courtes : 2 à 3 phrases maximum."
)


def build_system_prompt() -> str:
    """Prompt système envoyé une seule fois au démarrage."""
    return f"<|system|>\n{_SYSTEM_MESSAGE}<|end|>\n"


def build_user_prompt_fallback(question: str, hint: str = "") -> str:
    """Prompt ultra-court pour le niveau LLM (score < 0.55)."""
    if hint:
        body = (
            f"[Contexte approximatif]\n{hint}\n\n"
            f"Question: {question.strip()}\n"
            f"Réponds en 1-2 phrases."
        )
    else:
        body = (
            f"Question: {question.strip()}\n"
            f"Réponds que tu n'as pas l'information et oriente vers le secrétariat."
        )
    
    return f"<|user|>\n{body}<|end|>\n<|assistant|>\n"


# Test
if __name__ == "__main__":
    print("=== Test prompt_builder.py ===\n")
    print(build_system_prompt())
    print(build_user_prompt_fallback("Quels sont les frais ?", "Les frais sont de 500k FCFA"))
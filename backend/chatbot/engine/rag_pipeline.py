"""
rag_pipeline.py — Pipeline RAG à 3 niveaux :
    Niveau 1: CONV   → Réponses conversationnelles
    Niveau 2: DIRECT → Score FAISS ≥ 0.55 → réponse directe depuis la base
    Niveau 3: LLM    → Score < 0.55 → génération LLM (Ollama)
"""

import re
import sys
from pathlib import Path
from collections.abc import Iterator
from typing import Any

_ENGINE_DIR = Path(__file__).resolve().parent
if str(_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENGINE_DIR))

try:
    from .embedder import encode
    from .faiss_search import search_with_metadata, is_loaded as faiss_loaded
    from .llm_client_persistent import generate_stream, is_initialized as llm_initialized
    from .prompt_builder import build_user_prompt_fallback
except ImportError:
    from embedder import encode
    from faiss_search import search_with_metadata, is_loaded as faiss_loaded
    from llm_client_persistent import generate_stream, is_initialized as llm_initialized
    from prompt_builder import build_user_prompt_fallback

# Seuils et paramètres
SCORE_DIRECT = 0.55  # Au-dessus → réponse directe
FAISS_TOP_K = 1      # Un seul résultat suffit

# Niveau 1: Patterns conversationnels
_CONV_PATTERNS = [
    (r'\b(bonjour|salut|bonsoir|hello)\b',
     "Bonjour ! Je suis SUP'ONE, l'assistant du Club Informatique de SUP'PTIC."),
    (r'\b(merci|thank|thanks)\b',
     "Avec plaisir ! N'hésitez pas si vous avez d'autres questions."),
    (r'\b(au revoir|bye|bonne journée)\b',
     "Au revoir ! Bonne continuation à SUP'PTIC."),
    (r'\b(qui es-tu|ton nom|tu t\'appelles)\b',
     "Je suis SUP'ONE, l'assistant intelligent du Club Informatique de SUP'PTIC."),
    (r'\b(que peux-tu faire|aide-moi)\b',
     "Je réponds à vos questions sur SUP'PTIC : inscriptions, filières, frais, débouchés."),
]
_COMPILED_PATTERNS = [(re.compile(p, re.IGNORECASE), r) for p, r in _CONV_PATTERNS]


def _detect_conversational(question: str) -> str | None:
    """Niveau 1: Détection des questions conversationnelles."""
    q = question.strip()
    for pattern, response in _COMPILED_PATTERNS:
        if pattern.search(q):
            return response
    return None


def ask_stream(question: str, history: list[dict] | None = None) -> Iterator[str | dict]:
    """
    Pipeline RAG à 3 niveaux.
    
    Niveau 1 - CONV: Réponses conversationnelles immédiates
    Niveau 2 - DIRECT: Score FAISS >= 0.55 → réponse depuis la base
    Niveau 3 - LLM: Score < 0.55 → génération avec fallback TF-IDF
    """
    # Niveau 1: Réponses conversationnelles
    conv_response = _detect_conversational(question)
    if conv_response:
        yield {"type": "meta", "method": "CONV", "score": 1.0}
        yield conv_response
        yield {"type": "done"}
        return
    
    # Recherche FAISS
    query_vec = encode(question)
    contexts = []
    best_score = 0.0
    
    if faiss_loaded():
        contexts = search_with_metadata(query_vec, k=FAISS_TOP_K)
        best_score = contexts[0]["score"] if contexts else 0.0
    
    # Niveau 2: Réponse directe
    if best_score >= SCORE_DIRECT and contexts:
        best = contexts[0]
        yield {
            "type": "meta",
            "method": "DIRECT",
            "score": round(best_score, 4),
            "source": {
                "question": best.get("example", ""),
                "categorie": best.get("categorie", ""),
            }
        }
        yield best["response"]
        yield {"type": "done"}
        return
    
    # Niveau 3: LLM fallback
    yield {
        "type": "meta",
        "method": "LLM",
        "score": round(best_score, 4),
    }
    
    if not llm_initialized():
        yield "Je n'ai pas cette information. Contactez le secrétariat de SUP'PTIC."
        yield {"type": "done"}
        return
    
    user_prompt = build_user_prompt_fallback(question)
    for token in generate_stream(user_prompt, fallback=True):
        yield token
    yield {"type": "done"}


def build_sse_event(data: Any) -> str:
    """Format SSE pour streaming HTTP."""
    import json
    if isinstance(data, str):
        payload = json.dumps({"type": "token", "content": data}, ensure_ascii=False)
    else:
        payload = json.dumps(data, ensure_ascii=False)
    return f"data: {payload}\n\n"


# Test
if __name__ == "__main__":
    import faiss_search
    
    faiss_search.load_index()
    
    tests = [
        "Bonjour, qui es-tu ?",           # CONV
        "Quels sont les frais ?",         # DIRECT ou LLM
        "Quel temps fait-il ?",           # LLM fallback
    ]
    
    for q in tests:
        print(f"\nQuestion: {q}")
        for event in ask_stream(q):
            if isinstance(event, dict) and event.get("type") == "meta":
                print(f"  Méthode: {event['method']} | Score: {event.get('score', 0)}")
            elif isinstance(event, str):
                print(f"  Réponse: {event[:100]}")
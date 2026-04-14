from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.response import Response

# ── Pipeline RAG Phase 2 ─────────────────────────────────────────────────────
from chatbot.engine.rag_pipeline import ask, ask_stream, build_sse_event

# ── Fallback Phase 1 (conservé) ───────────────────────────────────────────────
from .services import get_chatbot_response


# ════════════════════════════════════════════════════════════════════════════
# ENDPOINT PRINCIPAL — POST /api/chatbot/ask/
# ════════════════════════════════════════════════════════════════════════════

@api_view(["POST"])
def ask_chatbot(request):
    """Endpoint pour poser une question au chatbot."""
    user_query = request.data.get("question")
    if not user_query:
        return Response({"error": "La question est vide"}, status=400)

    intent_model, intents = _get_intent_model()

    # Étape 1 : Détection d'intent (si modèle disponible)
    if intent_model is not None and intents:
        try:
            intent, confidence, response = detect_intent(user_query, intent_model, intents)
            if confidence >= 0.8:
                return Response({
                    "question": user_query,
                    "intent": intent,
                    "response": response,
                    "confidence": confidence,
                })
        except Exception:
            pass  # Fallback silencieux vers TF-IDF

    # Étape 2 : Fallback TF-IDF + similarité cosinus
    result = get_chatbot_response(user_query)
    return Response(result)

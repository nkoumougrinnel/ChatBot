"""
views.py — Endpoints API du chatbot SUP'ONE.

Phase 1 (conservé) :
    POST /api/chatbot/ask/        → TF-IDF + intent detection

Phase 2 (ajouté J6) :
    POST /api/chatbot/ask/        → Pipeline RAG (MiniLM → FAISS → Phi-3)
                                    avec streaming SSE et fallback TF-IDF automatique
    POST /api/feedback/           → Enregistrement like/dislike
    GET  /api/stats/              → Statistiques d'usage
    POST /api/reload-index/       → Rechargement FAISS à chaud
"""

import json

from django.http import StreamingHttpResponse
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
    """
    Endpoint principal du chatbot — Phase 2 RAG.

    Corps de la requête (JSON) :
        {
            "question": "C'est combien pour s'inscrire ?",
            "history":  [                              ← optionnel
                {"role": "user",      "content": "..."},
                {"role": "assistant", "content": "..."}
            ],
            "stream": true                             ← optionnel, défaut false
        }

    Réponse sans streaming :
        {
            "answer":     "Les frais s'élèvent à...",
            "sources":    [{"question": "...", "score": 0.87, "categorie": "...", "source": "..."}],
            "method":     "RAG",
            "best_score": 0.87
        }

    Réponse avec streaming (stream=true) :
        Content-Type: text/event-stream
        data: {"type": "meta",  "method": "RAG", "sources": [...], "best_score": 0.87}\n\n
        data: {"type": "token", "content": "Les "}\n\n
        data: {"type": "token", "content": "frais "}\n\n
        ...
        data: {"type": "done"}\n\n
    """
    question = request.data.get("question", "").strip()
    if not question:
        return Response({"error": "La question est vide."}, status=400)

    history = request.data.get("history", None)
    stream  = request.data.get("stream", False)

    # ── Mode streaming SSE ────────────────────────────────────────────────
    if stream:
        def event_stream():
            try:
                for chunk in ask_stream(question, history):
                    yield build_sse_event(chunk)
            except Exception as e:
                error_event = build_sse_event({"type": "error", "message": str(e)})
                yield error_event

        response = StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream"
        )
        response["Cache-Control"]               = "no-cache"
        response["X-Accel-Buffering"]           = "no"   # désactive le buffer Nginx
        response["Access-Control-Allow-Origin"] = "*"
        return response

    # ── Mode réponse complète (non streamé) ───────────────────────────────
    try:
        result = ask(question, history)
        return Response(result, status=200)
    except Exception as e:
        return Response({"error": f"Erreur pipeline RAG : {str(e)}"}, status=500)


# ════════════════════════════════════════════════════════════════════════════
# ENDPOINT FEEDBACK — POST /api/feedback/
# ════════════════════════════════════════════════════════════════════════════

@api_view(["POST"])
def submit_feedback(request):
    """
    Enregistre un feedback like/dislike sur une réponse du chatbot.

    Corps de la requête (JSON) :
        {
            "message_id": "abc123",
            "type":       "like" | "dislike",
            "method":     "RAG" | "TF-IDF"    ← optionnel
        }
    """
    message_id = request.data.get("message_id", "")
    fb_type    = request.data.get("type", "")
    method     = request.data.get("method", "")

    if fb_type not in ("like", "dislike"):
        return Response(
            {"error": "Le champ 'type' doit valoir 'like' ou 'dislike'."},
            status=400
        )

    try:
        from chatbot.models import Feedback
        Feedback.objects.create(
            message_id = message_id,
            fb_type    = fb_type,
            rag_method = method,
        )
        return Response({"status": "ok"}, status=201)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ════════════════════════════════════════════════════════════════════════════
# ENDPOINT STATS — GET /api/stats/
# ════════════════════════════════════════════════════════════════════════════

@api_view(["GET"])
def get_stats(request):
    """
    Retourne les statistiques d'usage du chatbot.

    Réponse :
        {
            "total_questions":  142,
            "rag_count":        98,
            "tfidf_count":      44,
            "likes":            87,
            "dislikes":         12,
            "index_stats":      {"ntotal": 420, "dim": 384, "loaded": true}
        }
    """
    try:
        from chatbot.models import Feedback
        from chatbot.engine.faiss_search import get_index_stats

        likes    = Feedback.objects.filter(fb_type="like").count()
        dislikes = Feedback.objects.filter(fb_type="dislike").count()
        rag      = Feedback.objects.filter(rag_method="RAG").count()
        tfidf    = Feedback.objects.filter(rag_method="TF-IDF").count()

        return Response({
            "total_feedbacks": likes + dislikes,
            "rag_count":       rag,
            "tfidf_count":     tfidf,
            "likes":           likes,
            "dislikes":        dislikes,
            "index_stats":     get_index_stats(),
        }, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ════════════════════════════════════════════════════════════════════════════
# ENDPOINT RELOAD INDEX — POST /api/reload-index/
# ════════════════════════════════════════════════════════════════════════════

@api_view(["POST"])
def reload_index(request):
    """
    Recharge l'index FAISS à chaud sans redémarrer Django.
    À appeler après un rebuild de l'index (build_index.py).

    Réponse :
        {"status": "ok", "message": "Index rechargé : 420 vecteurs"}
    """
    try:
        from chatbot.engine.faiss_search import reload_index as faiss_reload
        faiss_reload()
        from chatbot.engine.faiss_search import get_index_stats
        stats = get_index_stats()
        return Response({
            "status":  "ok",
            "message": f"Index rechargé : {stats['ntotal']} vecteurs",
            "stats":   stats,
        }, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

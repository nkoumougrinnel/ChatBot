"""
views.py — Endpoints API du chatbot SUP'ONE Phase 2.

    POST /api/chatbot/ask/   → Pipeline RAG (MiniLM → FAISS → Phi-3) + streaming SSE
    POST /api/feedback/      → Enregistrement like/dislike
    GET  /api/stats/rag/     → Statistiques d'usage + état index FAISS
    POST /api/reload-index/  → Rechargement FAISS à chaud sans redémarrer Django
"""

import os

from django.http import StreamingHttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

# ── Mode hors ligne HuggingFace ───────────────────────────────────────────────
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE",  "1")

# ── Pipeline RAG Phase 2 ──────────────────────────────────────────────────────
from chatbot.engine.rag_pipeline import ask, ask_stream, build_sse_event
from chatbot.engine import faiss_search, tfidf_fallback

# ── Chargement manuel des moteurs ─────────────────────────────────────────────
if not faiss_search.is_loaded():
    faiss_search.load_index()

if not tfidf_fallback.is_loaded():
    tfidf_fallback.load()


# ════════════════════════════════════════════════════════════════════════════
# ENDPOINT PRINCIPAL — POST /api/chatbot/ask/
# ════════════════════════════════════════════════════════════════════════════

@api_view(["POST"])
def ask_chatbot(request):
    """
    Endpoint principal du chatbot — Phase 2 RAG.

    Corps JSON :
        {
            "question": "C'est combien pour s'inscrire ?",
            "stream":   false,
            "history":  [{"role": "user", "content": "..."}]  <- optionnel
        }
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
                yield build_sse_event({"type": "error", "message": str(e)})

        response = StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream"
        )
        response["Cache-Control"]               = "no-cache"
        response["X-Accel-Buffering"]           = "no"
        response["Access-Control-Allow-Origin"] = "*"
        return response

    # ── Mode réponse complète ─────────────────────────────────────────────
    try:
        result = ask(question, history)
        return Response(result, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ════════════════════════════════════════════════════════════════════════════
# ENDPOINT FEEDBACK — POST /api/feedback/
# ════════════════════════════════════════════════════════════════════════════

@api_view(["POST"])
def submit_feedback(request):
    """
    Enregistre un feedback like/dislike.

    Corps JSON :
        {"message_id": "abc123", "type": "like", "method": "RAG"}
    """
    fb_type = request.data.get("type", "")
    if fb_type not in ("like", "dislike"):
        return Response(
            {"error": "Le champ 'type' doit valoir 'like' ou 'dislike'."},
            status=400
        )
    try:
        from chatbot.models import Feedback
        Feedback.objects.create(
            message_id = request.data.get("message_id", ""),
            fb_type    = fb_type,
            rag_method = request.data.get("method", ""),
        )
        return Response({"status": "ok"}, status=201)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ════════════════════════════════════════════════════════════════════════════
# ENDPOINT STATS — GET /api/stats/rag/
# ════════════════════════════════════════════════════════════════════════════

@api_view(["GET"])
def get_stats(request):
    """Retourne les statistiques d'usage et l'état de l'index FAISS."""
    try:
        from chatbot.models import Feedback
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
            "index_stats":     faiss_search.get_index_stats(),
        }, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ════════════════════════════════════════════════════════════════════════════
# ENDPOINT RELOAD INDEX — POST /api/reload-index/
# ════════════════════════════════════════════════════════════════════════════

@api_view(["POST"])
def reload_index(request):
    """Recharge l'index FAISS à chaud sans redémarrer Django."""
    try:
        faiss_search.reload_index()
        tfidf_fallback.rebuild()
        stats = faiss_search.get_index_stats()
        return Response({
            "status":  "ok",
            "message": f"Index rechargé : {stats['ntotal']} vecteurs",
            "stats":   stats,
        }, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
"""
views.py — Endpoints API du chatbot SUP'ONE.

Chaque événement SSE envoyé au frontend est un objet JSON avec un champ `type` :

    { "type": "status",  "status": "thinking"|"searching"|"streaming" }
        → Animation côté frontend (indicateur de chargement, recherche, etc.)

    { "type": "meta",    "method": "CONV"|"DIRECT"|"LLM", "score": float,
                         "source": { "question": str, "categorie": str } | null }
        → Permet au frontend de choisir l'animation de bulle (ex: badge méthode RAG)

    { "type": "token",   "content": str }
        → Fragment de texte à ajouter progressivement dans la bulle

    { "type": "done",    "elapsed_ms": int }
        → Fin de réponse ; le frontend arrête l'animation et affiche un bouton feedback

    { "type": "error",   "message": str }
        → Erreur à afficher dans la bulle
"""

import json
import time

from django.http import StreamingHttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from chatbot.engine.rag_pipeline import ask_stream
from chatbot.engine.llm_client_persistent import generate_stream, check_availability


# ---------------------------------------------------------------------------
# Helpers SSE
# ---------------------------------------------------------------------------

def _sse(payload: dict) -> str:
    """Sérialise un dict en ligne SSE (data: ...\n\n)."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@api_view(["GET"])
def llm_status(request):
    """
    Vérifie la disponibilité du serveur Ollama et du modèle.

    GET /api/chatbot/status/

    Response 200:
        {
            "available": bool,
            "model_loaded": bool,
            "model": str,
            "error": str | null
        }
    """
    return Response(check_availability())


@api_view(["POST"])
def ask_chatbot(request):
    """
    Pose une question au chatbot via le pipeline RAG en streaming SSE.

    POST /api/chatbot/ask/
    Body JSON : { "question": str, "history": list | null }

    Flux SSE émis dans l'ordre :
        1. status  → "thinking"   (démarrage immédiat, frontend affiche un loader)
        2. status  → "searching"  (FAISS en cours)
        3. meta    → méthode + score + source
        4. status  → "streaming"  (seulement pour LLM, avant les tokens)
        5. token*  → fragments de texte
        6. done    → elapsed_ms
    """
    question = request.data.get("question", "").strip()
    if not question:
        return Response({"error": "La question est vide"}, status=400)

    history = request.data.get("history")
    if history is not None and not isinstance(history, list):
        history = None

    def event_generator():
        t_start = time.time()

        # ── 1. Démarrage immédiat ──────────────────────────────────────────
        yield _sse({"type": "status", "status": "thinking"})

        try:
            pipeline = ask_stream(question, history)
            method = None

            for event in pipeline:
                # ── Événement de méta-données du pipeline ─────────────────
                if isinstance(event, dict):
                    ev_type = event.get("type")

                    if ev_type == "meta":
                        method = event.get("method")

                        # Juste avant la meta, on indique "searching" pour FAISS
                        if method in ("DIRECT", "LLM"):
                            yield _sse({"type": "status", "status": "searching"})

                        # Transmet la meta au frontend
                        yield _sse({
                            "type": "meta",
                            "method": method,
                            "score": event.get("score", 0.0),
                            "source": event.get("source"),   # None pour LLM/CONV
                        })

                        # Si LLM, on préviendra juste avant le premier token
                        if method == "LLM":
                            yield _sse({"type": "status", "status": "streaming"})

                    elif ev_type == "done":
                        elapsed = round((time.time() - t_start) * 1000)
                        yield _sse({"type": "done", "elapsed_ms": elapsed})

                # ── Fragment de texte ──────────────────────────────────────
                elif isinstance(event, str):
                    yield _sse({"type": "token", "content": event})

        except Exception as exc:  # noqa: BLE001
            yield _sse({"type": "error", "message": str(exc)})
            elapsed = round((time.time() - t_start) * 1000)
            yield _sse({"type": "done", "elapsed_ms": elapsed})

    return StreamingHttpResponse(
        event_generator(),
        content_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@api_view(["POST"])
def test_llm_latency(request):
    """
    Mesure la latence brute du LLM (debug uniquement).

    POST /api/chatbot/test-llm/
    Body JSON : { "prompt": str }

    Response 200:
        {
            "prompt_length": int,
            "response": str,
            "llm_time": float,
            "response_length": int
        }
    """
    prompt = request.data.get("prompt", "").strip()
    if not prompt:
        return Response({"error": "Prompt vide"}, status=400)

    try:
        t_start = time.time()
        response_text = "".join(generate_stream(prompt))
        llm_time = round(time.time() - t_start, 2)

        return Response({
            "prompt_length": len(prompt),
            "response": response_text,
            "llm_time": llm_time,
            "response_length": len(response_text),
        })
    except Exception as exc:  # noqa: BLE001
        return Response({"error": str(exc)}, status=500)
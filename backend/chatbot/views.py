"""
views.py — Endpoints API du chatbot SUP'ONE.
Génération 3 — pipeline 4 niveaux avec LLM réactivé au niveau OFFBASE.

Protocole SSE émis par ask_stream() :

    event: start
    data: <level>|<method>     → ex: "direct|faiss_direct", "llm|llm_phi3", "offbase|offbase"

    data: <token>              → token(s) de la réponse (un par un pour le LLM, en bloc sinon)

    event: done
    data: <latency_ms>         → fin du stream

    event: error
    data: <message>            → erreur système

Ce que views.py retransmet au frontend (JSON) :

    { "type": "status",  "status": "thinking"|"searching"|"generating" }
    { "type": "meta",    "method": str, "score": float, "level": str }
    { "type": "token",   "content": str }
    { "type": "done",    "elapsed_ms": int }
    { "type": "error",   "message": str }
"""

import json
import time

from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response

def _pipeline():
    from chatbot.engine.rag_pipeline import ask, ask_stream, health
    return ask, ask_stream, health


def _llm():
    from chatbot.engine.llm_client import check_availability, generate_stream
    return check_availability, generate_stream


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sse(payload: dict) -> str:
    """Sérialise un dict en ligne SSE JSON (data: ...\n\n)."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


# Correspondance level → label lisible pour le frontend
_LEVEL_TO_METHOD = {
    "conv":    "CONV",
    "direct":  "DIRECT",
    "tfidf":   "TF-IDF",
    "llm":     "LLM",
    "offbase": "OFFBASE",
}

# Niveaux qui déclenchent le statut "searching" (FAISS consulté)
_FAISS_LEVELS = {"direct", "tfidf", "llm", "offbase"}

# Niveau qui déclenche le statut "generating" (LLM en cours)
_LLM_LEVEL = "llm"


def _parse_sse_line(raw: str) -> tuple[str | None, str | None]:
    """Parse une ligne SSE brute produite par build_sse_event()."""
    event_name = None
    data_value = None
    for line in raw.strip().split("\n"):
        if line.startswith("event:"):
            event_name = line[len("event:"):].strip()
        elif line.startswith("data:"):
            data_value = line[len("data:"):].strip()
    return event_name, data_value


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@api_view(["GET"])
def llm_status(request):
    """
    Vérifie la disponibilité du LLM (Gemini) et l'état général du pipeline.

    GET /api/v2/chatbot/status/

    Response 200 :
        {
            "available": bool,
            "model": str,
            "error": str | null,
            "pipeline": { faiss_loaded, tfidf_loaded, ready, ... }
        }
    """
    check_availability, _ = _llm()
    _, _, pipeline_health_fn = _pipeline()
    llm      = check_availability()
    pipeline = pipeline_health_fn()
    return Response({**llm, "pipeline": pipeline})


@csrf_exempt
def ask_chatbot(request):
    """
    Pose une question au chatbot via le pipeline Gen3 (4 niveaux).

    POST /api/chatbot/ask/
    Body JSON : { "question": str, "history": list | null, "stream": bool }

    stream=true  (défaut) → SSE text/event-stream
    stream=false           → JSON classique
    """
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée."}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Body JSON invalide."}, status=400)

    question = body.get("question", "").strip()
    if not question:
        return JsonResponse({"error": "La question est vide."}, status=400)

    history = body.get("history")
    if history is not None and not isinstance(history, list):
        history = None

    use_stream = body.get("stream", True)

    # ── Mode JSON (non streamé) ──────────────────────────────────────────────
    if use_stream is False:
        try:
            ask_fn, _, _ = _pipeline()
            result = ask_fn(question, history)
            return JsonResponse({
                "answer":     result.answer,
                "method":     _LEVEL_TO_METHOD.get(result.level, result.level.upper()),
                "level":      result.level,
                "score":      round(result.score, 4),
                "latency_ms": result.latency_ms,
                "source":     result.source,
                "categorie":  result.categorie,
            })
        except Exception as exc:
            return JsonResponse({"error": str(exc)}, status=500)

    # ── Mode SSE (streaming) ─────────────────────────────────────────────────
    def event_generator():
        t_start = time.time()

        # Statut immédiat
        yield _sse({"type": "status", "status": "thinking"})

        try:
            _, ask_stream_fn, _ = _pipeline()
            for raw in ask_stream_fn(question, history):
                event_name, data = _parse_sse_line(raw)

                # event: start → métadonnées du pipeline
                if event_name == "start" and data:
                    parts  = data.split("|", 1)
                    level  = parts[0]
                    method = _LEVEL_TO_METHOD.get(level, level.upper())

                    if level in _FAISS_LEVELS:
                        yield _sse({"type": "status", "status": "searching"})

                    # Statut "generating" spécifique au LLM
                    if level == _LLM_LEVEL:
                        yield _sse({"type": "status", "status": "generating"})

                    yield _sse({
                        "type":   "meta",
                        "level":  level,
                        "method": method,
                        "score":  0.0,
                    })

                # event: done → fin du stream
                elif event_name == "done" and data:
                    elapsed = round((time.time() - t_start) * 1000)
                    yield _sse({"type": "done", "elapsed_ms": elapsed})

                # event: error → erreur système
                elif event_name == "error" and data:
                    yield _sse({"type": "error", "message": data})
                    elapsed = round((time.time() - t_start) * 1000)
                    yield _sse({"type": "done", "elapsed_ms": elapsed})

                # data seul → token de réponse
                elif event_name is None and data:
                    yield _sse({"type": "token", "content": data})

        except RuntimeError as exc:
            yield _sse({"type": "error", "message": str(exc)})
            elapsed = round((time.time() - t_start) * 1000)
            yield _sse({"type": "done", "elapsed_ms": elapsed})

        except Exception as exc:
            yield _sse({"type": "error", "message": f"Erreur inattendue : {exc}"})
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
    """
    prompt = request.data.get("prompt", "").strip()
    if not prompt:
        return Response({"error": "Prompt vide."}, status=400)

    try:
        t_start = time.time()
        _, generate_stream_fn = _llm()
        response_text = "".join(generate_stream_fn(prompt, level="llm"))
        llm_time = round(time.time() - t_start, 2)
        return Response({
            "prompt_length":   len(prompt),
            "response":        response_text,
            "llm_time_s":      llm_time,
            "response_length": len(response_text),
        })
    except Exception as exc:
        return Response({"error": str(exc)}, status=500)


@api_view(["GET"])
def reload_index(request):
    """
    Recharge l'index FAISS à chaud sans redémarrer Django.

    GET /api/chatbot/reload-index/
    """
    try:
        from chatbot.engine.faiss_search import reload_index as _reload, get_index_stats
        _reload()
        stats = get_index_stats()
        return Response({"status": "reloaded", "ntotal": stats["ntotal"]})
    except Exception as exc:
        return Response({"error": str(exc)}, status=500)
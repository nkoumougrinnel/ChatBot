"""
views.py — Endpoints API du chatbot SUP'ONE.
Génération 3 — adapté au protocole SSE de ask_stream() / build_sse_event().

Protocole SSE émis par ask_stream() :

    event: start
    data: <level>|<method>          → ex: "direct|faiss_direct", "tfidf|tfidf_direct"

    data: <texte de la réponse>     → token(s) de la réponse

    event: done
    data: <latency_ms>              → fin du stream

    event: error
    data: <message>                 → erreur système (TF-IDF absent, etc.)

Ce que views.py fait :
    - parse chaque ligne SSE brute produite par ask_stream()
    - retransmet au frontend sous forme de JSON enrichi :

    { "type": "status",  "status": "thinking"|"searching" }
    { "type": "meta",    "method": str, "score": float, "level": str }
    { "type": "token",   "content": str }
    { "type": "done",    "elapsed_ms": int }
    { "type": "error",   "message": str }
"""

import json
import time

from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response

from chatbot.engine.rag_pipeline import ask_stream, health as pipeline_health
from chatbot.engine.llm_client import check_availability, generate_stream


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sse(payload: dict) -> str:
    """Sérialise un dict en ligne SSE JSON (data: ...\n\n)."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


# Correspondance level → label méthode lisible pour le frontend
_LEVEL_TO_METHOD = {
    "conv":    "CONV",
    "direct":  "DIRECT",
    "tfidf":   "TF-IDF",
    "offbase": "OFFBASE",
    "llm":     "LLM",
}

# Niveaux qui déclenchent un statut "searching" (FAISS a été interrogé)
_FAISS_LEVELS = {"direct", "tfidf", "offbase"}


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
    
    #Vérifie la disponibilité d'Ollama et de l'état général du pipeline.

    #GET /api/chatbot/status/

    #Response 200 :
    #    {
    #        "available": bool,
    #        "model": str,
    #        "error": str | null,
    #        "pipeline": { faiss_loaded, tfidf_loaded, ready, ... }
    #    }
    
    ollama = check_availability()
    pipeline = pipeline_health()
    return Response({**ollama, "pipeline": pipeline})


@csrf_exempt
def ask_chatbot(request):
    
    #Pose une question au chatbot via le pipeline Gen3 en streaming SSE.

    #POST /api/chatbot/ask/
    #Body JSON : { "question": str, "history": list | null }

    #Note : pas de @api_view ici — DRF exige Content-Type: application/json
    #pour parser request.data, ce qui provoque "Impossible de lier le paramètre
    #Headers" quand StreamingHttpResponse retourne text/event-stream.
    #On lit le body avec json.loads(request.body) — fonctionne sans header.
    
    if request.method != "POST":
        from django.http import JsonResponse
        return JsonResponse({"error": "Méthode non autorisée."}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        from django.http import JsonResponse
        return JsonResponse({"error": "Body JSON invalide."}, status=400)

    question = body.get("question", "").strip()
    if not question:
        from django.http import JsonResponse
        return JsonResponse({"error": "La question est vide."}, status=400)

    history = body.get("history")
    if history is not None and not isinstance(history, list):
        history = None

    def event_generator():
        t_start = time.time()

        # ── 1. Statut immédiat ─────────────────────────────────────────────
        yield _sse({"type": "status", "status": "thinking"})

        try:
            pending_event = None   # Nom du dernier event: lu (start/done/error)

            for raw in ask_stream(question, history):
                event_name, data = _parse_sse_line(raw)

                # ── event: start → métadonnées du pipeline ─────────────────
                if event_name == "start" and data:
                    parts  = data.split("|", 1)
                    level  = parts[0]                          # "direct", "tfidf"…
                    method = _LEVEL_TO_METHOD.get(level, level.upper())

                    # Statut "searching" si FAISS a été consulté
                    if level in _FAISS_LEVELS:
                        yield _sse({"type": "status", "status": "searching"})

                    yield _sse({
                        "type":   "meta",
                        "level":  level,
                        "method": method,
                        "score":  0.0,   # score disponible dans ask(), pas ask_stream()
                    })
                    pending_event = "start"

                # ── event: done → fin du stream ────────────────────────────
                elif event_name == "done" and data:
                    elapsed = round((time.time() - t_start) * 1000)
                    yield _sse({"type": "done", "elapsed_ms": elapsed})
                    pending_event = None

                # ── event: error → erreur système ──────────────────────────
                elif event_name == "error" and data:
                    yield _sse({"type": "error", "message": data})
                    elapsed = round((time.time() - t_start) * 1000)
                    yield _sse({"type": "done", "elapsed_ms": elapsed})
                    pending_event = None

                # ── data seul → token de réponse ───────────────────────────
                elif event_name is None and data:
                    yield _sse({"type": "token", "content": data})

        except RuntimeError as exc:
            # Erreur système levée par ask() si TF-IDF non chargé
            yield _sse({"type": "error", "message": str(exc)})
            elapsed = round((time.time() - t_start) * 1000)
            yield _sse({"type": "done", "elapsed_ms": elapsed})

        except Exception as exc:  # noqa: BLE001
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

    Response 200 :
        {
            "prompt_length": int,
            "response": str,
            "llm_time_s": float,
            "response_length": int
        }
    """
    prompt = request.data.get("prompt", "").strip()
    if not prompt:
        return Response({"error": "Prompt vide."}, status=400)

    try:
        t_start = time.time()
        response_text = "".join(generate_stream(prompt, level="llm"))
        llm_time = round(time.time() - t_start, 2)

        return Response({
            "prompt_length":   len(prompt),
            "response":        response_text,
            "llm_time_s":      llm_time,
            "response_length": len(response_text),
        })
    except Exception as exc:  # noqa: BLE001
        return Response({"error": str(exc)}, status=500)


@api_view(["GET"])
def reload_index(request):
    
    #Recharge l index FAISS à chaud sans redémarrer Django.

    #GET /api/chatbot/reload-index/

    #Response 200 : { "status": "reloaded", "ntotal": int }
    #Response 500 : { "error": str }
    
    try:
        from chatbot.engine.faiss_search import reload_index as _reload, get_index_stats
        _reload()
        stats = get_index_stats()
        return Response({"status": "reloaded", "ntotal": stats["ntotal"]})
    except Exception as exc:  # noqa: BLE001
        return Response({"error": str(exc)}, status=500)

"""
llm_client_persistent.py — Client Ollama avec session persistante.
"""

import json
import os
import urllib.error
import urllib.request
from collections.abc import Iterator

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "phi3:mini")

_FALLBACK_PARAMS = {
    "temperature": 0.1,
    "num_predict": 80,
    "num_ctx": 512,
    "stop": ["<|end|>", "<|user|>", "<|system|>"],
}

_session_prompt = ""
_session_initialized = False


def check_availability() -> dict:
    """
    Vérifie si le serveur Ollama est accessible et si le modèle est chargé.

    Returns:
        {
            "available": bool,        # True si Ollama répond
            "model_loaded": bool,     # True si le modèle cible est présent
            "model": str,             # Nom du modèle configuré
            "error": str | None,      # Message d'erreur si indisponible
        }
    """
    result = {
        "available": False,
        "model_loaded": False,
        "model": OLLAMA_MODEL,
        "error": None,
    }

    try:
        # Ping le endpoint /api/tags pour lister les modèles disponibles
        url = f"{OLLAMA_BASE_URL}/api/tags"
        req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            result["available"] = True

            # Vérifie que le modèle configuré est bien présent
            models = [m.get("name", "") for m in data.get("models", [])]
            result["model_loaded"] = any(
                m == OLLAMA_MODEL or m.startswith(OLLAMA_MODEL.split(":")[0])
                for m in models
            )

    except urllib.error.URLError as exc:
        result["error"] = f"Ollama inaccessible : {exc.reason}"
    except TimeoutError:
        result["error"] = "Timeout : Ollama ne répond pas sous 5 s"
    except Exception as exc:  # noqa: BLE001
        result["error"] = str(exc)

    return result


def init_session(system_prompt: str) -> None:
    """Initialise la session avec le prompt système."""
    global _session_prompt, _session_initialized
    _session_prompt = system_prompt
    _session_initialized = True
    print(f"[llm_client] Session initialisée ({len(system_prompt)} chars)")


def is_initialized() -> bool:
    return _session_initialized


def generate_stream(user_prompt: str, fallback: bool = False) -> Iterator[str]:
    """Génère une réponse en streaming."""
    if not _session_initialized:
        raise RuntimeError("Session non initialisée")

    full_prompt = _session_prompt + user_prompt
    params = _FALLBACK_PARAMS

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": True,
        "options": params,
    }

    url = f"{OLLAMA_BASE_URL}/api/generate"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    with urllib.request.urlopen(req, timeout=180) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if not line:
                continue
            try:
                chunk = json.loads(line)
                token = chunk.get("response", "")
                if token:
                    yield token
                if chunk.get("done"):
                    break
            except json.JSONDecodeError:
                continue


def close_session() -> None:
    global _session_prompt, _session_initialized
    _session_prompt = ""
    _session_initialized = False
"""
llm_client.py — Client HTTP pour Ollama (Phi-3 Mini).

Expose :
    generate(prompt)        -> str            (réponse complète)
    generate_stream(prompt) -> Iterator[str]  (tokens en continu)

Phi-3 Mini tourne entièrement en local via Ollama, sans appel externe.

Dépendance : pip install ollama  (ou appel HTTP direct, utilisé ici pour éviter
             la dépendance — compatible Ollama >= 0.1)
"""

import json
import os
from collections.abc import Iterator
from typing import Optional

import urllib.request
import urllib.error

# -------------------------------------------------------------------
# Configuration Ollama
# -------------------------------------------------------------------
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "phi3:mini")

# Paramètres de génération
_DEFAULT_PARAMS = {
    "temperature": 0.3,       # faible pour des réponses factuelles
    "num_predict": 150,        # reduit de 512->150
    "num_ctx": 512,
    "num_thread": 4,
    "num_gpu": 0,
    "stop": ["</s>", "[INST]", "[/INST]"],  # tokens d'arrêt Phi-3
    "top_p": 0.9,
}


def _post(endpoint: str, payload: dict, stream: bool = False):
    """
    Effectue un POST HTTP vers l'API Ollama.

    Args:
        endpoint: ex. "/api/generate"
        payload:  Corps de la requête (dict sérialisé en JSON).
        stream:   Si True, retourne l'objet réponse sans le lire entièrement.

    Returns:
        Si stream=False : dict (réponse JSON parsée).
        Si stream=True  : http.client.HTTPResponse (à itérer ligne par ligne).

    Raises:
        ConnectionError si Ollama n'est pas joignable.
        RuntimeError    si Ollama retourne une erreur HTTP.
    """
    url = f"{OLLAMA_BASE_URL}{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        response = urllib.request.urlopen(req, timeout=180)
    except urllib.error.URLError as exc:
        raise ConnectionError(
            f"[llm_client] Impossible de joindre Ollama à '{url}'. "
            f"Vérifiez qu'Ollama est lancé (ollama serve). Détail : {exc}"
        ) from exc

    if stream:
        return response  # l'appelant itère lui-même

    raw = response.read().decode("utf-8")
    return json.loads(raw)


def generate(prompt: str, model: str = OLLAMA_MODEL, **kwargs) -> str:
    """
    Génère une réponse complète (mode non-streamé).

    Args:
        prompt: Le prompt complet à envoyer au LLM.
        model:  Nom du modèle Ollama (default: phi3:mini).
        **kwargs: Paramètres de génération supplémentaires (surcharge _DEFAULT_PARAMS).

    Returns:
        Texte de la réponse (str).

    Raises:
        ConnectionError si Ollama n'est pas disponible.
    """
    params = {**_DEFAULT_PARAMS, **kwargs}
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": params,
    }
    response = _post("/api/generate", payload, stream=False)
    return response.get("response", "").strip()


def generate_stream(prompt: str, model: str = OLLAMA_MODEL, **kwargs) -> Iterator[str]:
    """
    Génère une réponse en streaming, token par token.

    Chaque élément yielded est un morceau de texte (peut contenir
    plusieurs mots ou un seul token, selon Ollama).

    Args:
        prompt: Le prompt complet.
        model:  Nom du modèle Ollama.
        **kwargs: Paramètres de génération supplémentaires.

    Yields:
        str — fragment de texte à afficher progressivement.

    Raises:
        ConnectionError si Ollama n'est pas disponible.
    """
    params = {**_DEFAULT_PARAMS, **kwargs}
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": params,
    }
    response = _post("/api/generate", payload, stream=True)
    try:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if not line:
                continue
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError:
                continue
            token = chunk.get("response", "")
            if token:
                yield token
            if chunk.get("done", False):
                break
    finally:
        response.close()


def check_availability(model: str = OLLAMA_MODEL) -> dict:
    """
    Vérifie que Ollama est lancé et que le modèle demandé est disponible.

    Returns:
        dict avec les clés : available (bool), model (str), error (str ou None).
    """
    try:
        url = f"{OLLAMA_BASE_URL}/api/tags"
        req = urllib.request.Request(url, method="GET")
        response = urllib.request.urlopen(req, timeout=5)
        data = json.loads(response.read().decode("utf-8"))
        models = [m.get("name", "") for m in data.get("models", [])]
        if any(model in m for m in models):
            return {"available": True, "model": model, "error": None}
        else:
            return {
                "available": False,
                "model": model,
                "error": f"Modèle '{model}' non trouvé. Lancez : ollama pull {model}",
            }
    except Exception as exc:
        return {"available": False, "model": model, "error": str(exc)}


# -------------------------------------------------------------------
# Test rapide (exécutable directement : python llm_client.py)
# -------------------------------------------------------------------
if __name__ == "__main__":
    import time

    print("=== Test llm_client.py ===\n")

    # 1. Vérification disponibilité
    status = check_availability()
    print(f"Disponibilité Ollama : {status}")
    if not status["available"]:
        print(f"ERREUR : {status['error']}")
        print("Assurez-vous qu'Ollama est lancé avec : ollama serve")
        exit(1)

    # 2. Test generate() — réponse complète
    print("\n--- Test generate() ---")
    test_prompt = (
        "Tu es un assistant de SUP'PTIC. Réponds uniquement en français.\n"
        "Question : Bonjour, comment ça va ?\n"
        "Réponse :"
    )
    t0 = time.time()
    result = generate(test_prompt)
    elapsed = time.time() - t0
    print(f"Réponse ({elapsed:.2f}s) : {result}")
    print(f"Latence:{elapsed:.2f}s (objectifs < 3s, CPU normal si > 3s)")

    # 3. Test generate_stream() — streaming
    print("\n--- Test generate_stream() ---")
    stream_prompt = (
        "Tu es un assistant de SUP'PTIC. Réponds en une phrase en français.\n"
        "Question : Quel est le nom de l'école ?\n"
        "Réponse :"
    )
    print("Réponse streamée : ", end="", flush=True)
    t0 = time.time()
    for token in generate_stream(stream_prompt):
        print(token, end="", flush=True)
    elapsed = time.time() - t0
    print(f"\n(durée : {elapsed:.2f}s)\n")

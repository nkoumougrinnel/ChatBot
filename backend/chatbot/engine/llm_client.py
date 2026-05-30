"""
llm_client.py — Client Gemini API (google-generativeai).
Génération 3 — remplacement d'Ollama par Gemini 1.5 Flash.

Interface publique (identique à l'ancienne version Ollama) :
    check_availability()              → dict
    generate(prompt, level, model)    → str
    generate_stream(prompt, level)    → Iterator[str]

Le reste du pipeline (rag_pipeline.py, views.py, prompt_builder.py)
n'est pas modifié. Seul ce fichier change.

Variables d'environnement :
    GEMINI_API_KEY   (obligatoire)
    GEMINI_MODEL     (défaut : gemini-1.5-flash)

Installation :
    pip install google-generativeai
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Iterator

import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError, ResourceExhausted, InvalidArgument

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("[llm_client] GEMINI_API_KEY non définie — le niveau LLM sera inactif.")

# -------------------------------------------------------------------
# Paramètres de génération par niveau
# Gemini utilise GenerationConfig, pas les paramètres Ollama.
# -------------------------------------------------------------------
_CONFIG_LLM = genai.types.GenerationConfig(
    temperature=0.3,
    max_output_tokens=512,
    top_p=0.90,
)

_CONFIG_DIRECT = genai.types.GenerationConfig(
    temperature=0.1,
    max_output_tokens=150,
    top_p=0.85,
)

_LEVEL_CONFIGS = {
    "llm":    _CONFIG_LLM,
    "direct": _CONFIG_DIRECT,
}

# -------------------------------------------------------------------
# Message système — identique à prompt_builder._SYSTEM_MESSAGE
# Gemini accepte un system_instruction séparé du prompt utilisateur.
# -------------------------------------------------------------------
_SYSTEM_INSTRUCTION = (
    "Tu es SUP'ONE, l'assistant officiel de SUP'PTIC, "
    "l'École Supérieure des Postes et Télécommunications du Cameroun.\n\n"
    "RÈGLES :\n"
    "1. Tu réponds UNIQUEMENT en français.\n"
    "2. Tu te bases EXCLUSIVEMENT sur le [CONTEXTE] fourni.\n"
    "3. Si l'information n'est PAS dans le [CONTEXTE], réponds EXACTEMENT : "
    "\"Je n'ai pas cette information dans ma base. Contactez le secrétariat de SUP'PTIC.\"\n"
    "4. Tu ne fabriques AUCUNE information.\n"
    "5. Tes réponses sont courtes : 2 à 3 phrases maximum."
)

# -------------------------------------------------------------------
# Circuit-breaker léger (identique à l'ancienne version Ollama)
# -------------------------------------------------------------------
_cb_failures   = 0
_cb_open_until = 0.0
_CB_THRESHOLD  = 3
_CB_RESET_S    = 30


def _check_circuit() -> None:
    if _cb_failures >= _CB_THRESHOLD and time.time() < _cb_open_until:
        remaining = int(_cb_open_until - time.time())
        raise RuntimeError(
            f"[llm_client] Circuit-breaker ouvert — Gemini en erreur. "
            f"Nouvelle tentative dans {remaining}s."
        )


def _record_success() -> None:
    global _cb_failures
    _cb_failures = 0


def _record_failure() -> None:
    global _cb_failures, _cb_open_until
    _cb_failures += 1
    if _cb_failures >= _CB_THRESHOLD:
        _cb_open_until = time.time() + _CB_RESET_S
        logger.warning("[llm_client] Circuit-breaker ouvert après %d échecs.", _cb_failures)


# -------------------------------------------------------------------
# Extraction du texte brut depuis la réponse Gemini
# -------------------------------------------------------------------
def _extract_text(response) -> str:
    """Extrait le texte d'une réponse Gemini (gère les cas de blocage)."""
    try:
        return response.text.strip()
    except ValueError:
        # Réponse bloquée par les filtres de sécurité Gemini
        finish = getattr(response.candidates[0], "finish_reason", "UNKNOWN") if response.candidates else "NO_CANDIDATE"
        logger.warning("[llm_client] Réponse Gemini bloquée (finish_reason=%s).", finish)
        return "Je n'ai pas cette information dans ma base. Contactez le secrétariat de SUP'PTIC."


# -------------------------------------------------------------------
# Génération complète (non streamée)
# -------------------------------------------------------------------
def generate(
    prompt: str,
    level:  str = "llm",
    model:  str = GEMINI_MODEL,
) -> str:
    """
    Génère une réponse complète via l'API Gemini.

    Args:
        prompt : prompt construit par build_prompt() — contient déjà
                 le [CONTEXTE] FAISS et la question de l'étudiant.
        level  : 'llm' ou 'direct' — détermine les paramètres de génération.
        model  : modèle Gemini à utiliser.

    Returns:
        Texte de la réponse nettoyé.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("[llm_client] GEMINI_API_KEY non définie.")

    _check_circuit()
    config = _LEVEL_CONFIGS.get(level, _CONFIG_LLM)

    try:
        gemini_model = genai.GenerativeModel(
            model_name=model,
            generation_config=config,
            system_instruction=_SYSTEM_INSTRUCTION,
        )
        response = gemini_model.generate_content(prompt)
        _record_success()
        logger.info("[llm_client] generate() OK — model=%s level=%s", model, level)
        return _extract_text(response)

    except ResourceExhausted as exc:
        _record_failure()
        logger.error("[llm_client] Quota Gemini dépassé : %s", exc)
        raise RuntimeError(f"[llm_client] Quota API Gemini dépassé : {exc}") from exc

    except InvalidArgument as exc:
        # Clé API invalide ou paramètre incorrect — ne pas enregistrer comme failure réseau
        logger.error("[llm_client] Paramètre invalide Gemini : %s", exc)
        raise RuntimeError(f"[llm_client] Paramètre invalide : {exc}") from exc

    except GoogleAPIError as exc:
        _record_failure()
        logger.error("[llm_client] Erreur API Gemini : %s", exc)
        raise RuntimeError(f"[llm_client] Erreur Gemini : {exc}") from exc

    except Exception as exc:
        _record_failure()
        logger.error("[llm_client] Erreur inattendue : %s", exc)
        raise


# -------------------------------------------------------------------
# Génération streamée token par token
# -------------------------------------------------------------------
def generate_stream(
    prompt: str,
    level:  str = "llm",
    model:  str = GEMINI_MODEL,
) -> Iterator[str]:
    """
    Génère une réponse Gemini en streaming.
    Yield chaque chunk de texte au fur et à mesure.

    Utilisé par rag_pipeline.ask_stream() pour le niveau LLM.
    Chaque chunk est retransmis au frontend via SSE (views.py).
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("[llm_client] GEMINI_API_KEY non définie.")

    _check_circuit()
    config = _LEVEL_CONFIGS.get(level, _CONFIG_LLM)

    try:
        gemini_model = genai.GenerativeModel(
            model_name=model,
            generation_config=config,
            system_instruction=_SYSTEM_INSTRUCTION,
        )
        response = gemini_model.generate_content(prompt, stream=True)
        _record_success()
        logger.info("[llm_client] generate_stream() démarré — model=%s level=%s", model, level)

        for chunk in response:
            try:
                text = chunk.text
                if text:
                    yield text
            except ValueError:
                # Chunk bloqué par les filtres de sécurité — on skippe proprement
                logger.warning("[llm_client] Chunk Gemini bloqué — skip.")
                continue

    except ResourceExhausted as exc:
        _record_failure()
        logger.error("[llm_client] Quota Gemini dépassé : %s", exc)
        raise RuntimeError(f"[llm_client] Quota API Gemini dépassé : {exc}") from exc

    except GoogleAPIError as exc:
        _record_failure()
        logger.error("[llm_client] Erreur API Gemini (stream) : %s", exc)
        raise RuntimeError(f"[llm_client] Erreur Gemini : {exc}") from exc

    except Exception as exc:
        _record_failure()
        logger.error("[llm_client] Erreur inattendue (stream) : %s", exc)
        raise


# -------------------------------------------------------------------
# Health check — ping l'API Gemini avec la clé configurée
# -------------------------------------------------------------------
def check_availability(model: str = GEMINI_MODEL) -> dict:
    """
    Vérifie que la clé Gemini est valide et que le modèle est accessible.

    Interface identique à l'ancienne version Ollama :
        { "available": bool, "model": str, "error": str|None }

    Stratégie : appel list_models() — pas de génération, pas de token consommé.
    """
    result = {"available": False, "model": model, "error": None}

    if not GEMINI_API_KEY:
        result["error"] = "GEMINI_API_KEY non définie dans les variables d'environnement."
        return result

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        available_models = [m.name for m in genai.list_models()]
        # Les noms sont de la forme "models/gemini-1.5-flash"
        model_found = any(model in m for m in available_models)

        if model_found:
            result["available"] = True
        else:
            result["error"] = (
                f"Modèle '{model}' non trouvé. "
                f"Modèles disponibles : {', '.join(available_models[:5])}…"
            )

    except InvalidArgument:
        result["error"] = "Clé API Gemini invalide. Vérifiez GEMINI_API_KEY."
    except GoogleAPIError as exc:
        result["error"] = f"Erreur API Gemini : {exc}"
    except Exception as exc:
        result["error"] = str(exc)

    return result


# -------------------------------------------------------------------
# Test rapide (python llm_client.py)
# -------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    print("=== Test llm_client.py — Gemini API ===\n")

    status = check_availability()
    print(f"Disponibilité : {status}")

    if not status["available"]:
        print(f"\nERREUR : {status['error']}")
        print("Vérifiez que GEMINI_API_KEY est définie et valide.")
        sys.exit(1)

    # Test generate() — non streamé
    test_prompt = (
        "[CONTEXTE]\n"
        "[1] Admissions | e-supptic.cm\n"
        "Les frais de scolarité à SUP'PTIC s'élèvent à 500 000 FCFA par an, "
        "payables en deux tranches.\n\n"
        "Question : C'est combien pour s'inscrire ?\n"
        "Réponds uniquement à partir du [CONTEXTE], en français, de façon concise.\n"
    )

    print("\n--- generate() ---")
    t0 = time.time()
    try:
        answer = generate(test_prompt, level="llm")
        print(f"Réponse ({time.time() - t0:.2f}s) : {answer}")
    except Exception as e:
        print(f"ERREUR : {e}")
        sys.exit(1)

    # Test generate_stream() — streamé
    print("\n--- generate_stream() ---")
    t0 = time.time()
    try:
        print("Réponse : ", end="", flush=True)
        for token in generate_stream(test_prompt, level="llm"):
            print(token, end="", flush=True)
        print(f"\n({time.time() - t0:.2f}s)")
    except Exception as e:
        print(f"\nERREUR : {e}")
        sys.exit(1)

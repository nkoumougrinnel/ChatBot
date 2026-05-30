"""
Suite de tests complète Gen3 — pipeline + API HTTP.
Usage (depuis backend/) :
    python scripts/run_full_test_suite.py
    python scripts/run_full_test_suite.py --base-url http://127.0.0.1:8000
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

# ── Chemins ──────────────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _SCRIPT_DIR.parent
_REPO_ROOT = _BACKEND_DIR.parent
_ENGINE = _BACKEND_DIR / "chatbot" / "engine"

for _p in [str(_ENGINE), str(_BACKEND_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("RAG_DATA_DIR", str(_BACKEND_DIR / "rag_data"))
os.environ.setdefault("FAQ_DATA_DIR", str(_REPO_ROOT / "data" / "json" / "validated"))

BASE_URL = "http://127.0.0.1:8000"


@dataclass
class Result:
    group: str
    name: str
    status: str  # OK | FAIL | SKIP | WARN
    detail: str = ""


results: list[Result] = []


def record(group: str, name: str, status: str, detail: str = "") -> None:
    results.append(Result(group, name, status, detail))
    icon = {"OK": "✔", "FAIL": "✘", "SKIP": "⊘", "WARN": "⚠"}.get(status, "?")
    line = f"  {icon}  [{group}] {name}"
    if detail:
        line += f" — {detail}"
    print(line)


# ── Pipeline (ask() direct) ──────────────────────────────────────────────────
def setup_pipeline():
    from faiss_search import load_index
    from tfidf_fallback import load as tfidf_load

    load_index()
    tfidf_load()


def test_pipeline():
    from rag_pipeline import ask

    print("\n" + "=" * 60)
    print("  PIPELINE — ask() direct")
    print("=" * 60)

    conv_cases = [
        "bonjour", "Bonsoir !", "Hello", "salut", "Merci beaucoup",
        "Au revoir", "Qui es-tu ?", "Comment tu t'appelles ?", "aide", "?",
    ]
    for q in conv_cases:
        r = ask(q)
        if r.level == "conv":
            record("CONV", q[:40], "OK", f"method={r.method}")
        else:
            record("CONV", q[:40], "FAIL", f"level={r.level}")

    conv_traps = [
        ("Bonjour, quels sont les frais de scolarité ?", "conv"),
        ("Merci, et pour l'inscription ?", "conv"),
    ]
    for q, expected in conv_traps:
        r = ask(q)
        if r.level == expected:
            record("CONV-PIÈGE", q[:45], "OK")
        else:
            record("CONV-PIÈGE", q[:45], "FAIL", f"attendu={expected}, got={r.level}")

    direct_cases = [
        "Quels sont les frais de scolarité à SUP'PTIC ?",
        "Comment obtenir une attestation de scolarité ?",
        "C'est combien pour s'inscrire ?",
        "Quelles sont les conditions d'admission ?",
        "Comment s'inscrire au SUP'PTIC ?",
        "Quand ont lieu les examens ?",
        "Comment sont calculées les notes ?",
        "Quelles filières existent à SUP'PTIC ?",
        "Quelle est l'histoire de SUP'PTIC ?",
        "Comment rejoindre le club informatique ?",
        "Où demander une attestation de scolarité ?",
    ]
    for q in direct_cases:
        r = ask(q)
        if r.level == "direct" and r.score >= 0.55:
            record("DIRECT", q[:45], "OK", f"score={r.score:.3f}")
        elif r.level == "direct":
            record("DIRECT", q[:45], "WARN", f"direct mais score={r.score:.3f}")
        elif r.level == "tfidf":
            record("DIRECT", q[:45], "WARN", f"tfidf à la place (score={r.score:.3f})")
        else:
            record("DIRECT", q[:45], "FAIL", f"level={r.level}, score={r.score:.3f}")

    tfidf_cases = [
        "tarif scol", "frais inscription", "comment register suptptic",
        "délai relevé notes", "attestation scolarité comment",
        "inscription supptic conditions", "calendrier exam",
    ]
    for q in tfidf_cases:
        r = ask(q)
        if r.level == "tfidf":
            record("TF-IDF", q[:40], "OK", f"score={r.score:.3f}")
        elif r.level == "direct":
            record("TF-IDF", q[:40], "WARN", f"direct (score={r.score:.3f}) — FAISS fort")
        else:
            record("TF-IDF", q[:40], "FAIL", f"level={r.level}, score={r.score:.3f}")

    offbase_cases = [
        "Quel temps fait-il aujourd'hui ?",
        "Quelle est la capitale de la France ?",
        "Recette de crêpes",
        "Qui a gagné la CAN 2024 ?",
        "Comment hacker un wifi ?",
        "Prix du bitcoin aujourd'hui",
    ]
    for q in offbase_cases:
        r = ask(q)
        if r.level == "offbase":
            record("OFFBASE", q[:40], "OK", f"score={r.score:.3f}")
        else:
            record("OFFBASE", q[:40], "FAIL", f"level={r.level}, score={r.score:.3f}")

    # Robustesse
    long_q = "Quels sont les frais " + "de scolarité " * 50 + "?"
    r = ask(long_q)
    record("ROBUSTESSE", "Question très longue", "OK" if r.answer else "FAIL")

    r = ask("C'est combien ??? !!! @#$")
    record("ROBUSTESSE", "Caractères spéciaux", "OK" if r.answer else "FAIL", f"level={r.level}")

    r = ask("FRAIS SCOLARITÉ supptic")
    record("ROBUSTESSE", "Accents / casse", "OK" if r.level in ("direct", "tfidf") else "WARN", f"level={r.level}")

    t0 = ask("Quels sont les frais de scolarité ?")
    t1 = ask("Quels sont les frais de scolarité ?")
    if t1.latency_ms <= t0.latency_ms or t1.answer == t0.answer:
        record("ROBUSTESSE", "Cache embedder (2× même question)", "OK", f"{t0.latency_ms}ms → {t1.latency_ms}ms")
    else:
        record("ROBUSTESSE", "Cache embedder", "WARN", "latence non réduite")

    r = ask("bonjour")
    record("ROBUSTESSE", "history ignoré (pipeline)", "OK" if r.level == "conv" else "FAIL")


def _ask_api(question: str) -> dict | None:
    try:
        _, text, _ = http_post("/api/chatbot/ask/", {"question": question, "stream": False}, timeout=180)
        return json.loads(text)
    except Exception:
        return None


def test_pipeline_via_api():
    """Exécute les cas pipeline via POST /api/chatbot/ask/ (stream=false)."""
    print("\n" + "=" * 60)
    print("  PIPELINE — via API HTTP")
    print("=" * 60)

    conv_cases = [
        "bonjour", "Bonsoir !", "Hello", "salut", "Merci beaucoup",
        "Au revoir", "Qui es-tu ?", "Comment tu t'appelles ?", "aide", "?",
    ]
    for q in conv_cases:
        d = _ask_api(q)
        if d and d.get("level") == "conv":
            record("CONV", q[:40], "OK", f"method={d.get('method')}")
        else:
            record("CONV", q[:40], "FAIL", str(d)[:60] if d else "pas de réponse")

    for q in ("Bonjour, quels sont les frais de scolarité ?", "Merci, et pour l'inscription ?"):
        d = _ask_api(q)
        if d and d.get("level") == "conv":
            record("CONV-PIÈGE", q[:45], "OK")
        else:
            record("CONV-PIÈGE", q[:45], "FAIL", f"level={d.get('level') if d else '?'}")

    direct_cases = [
        "Quels sont les frais de scolarité à SUP'PTIC ?",
        "Comment obtenir une attestation de scolarité ?",
        "C'est combien pour s'inscrire ?",
        "Quelles sont les conditions d'admission ?",
        "Comment s'inscrire au SUP'PTIC ?",
        "Quand ont lieu les examens ?",
        "Comment sont calculées les notes ?",
        "Quelles filières existent à SUP'PTIC ?",
        "Quelle est l'histoire de SUP'PTIC ?",
        "Comment rejoindre le club informatique ?",
        "Où demander une attestation de scolarité ?",
    ]
    for q in direct_cases:
        d = _ask_api(q)
        if not d:
            record("DIRECT", q[:45], "FAIL", "pas de réponse")
        elif d.get("level") == "direct" and (d.get("score") or 0) >= 0.55:
            record("DIRECT", q[:45], "OK", f"score={d.get('score')}")
        elif d.get("level") == "direct":
            record("DIRECT", q[:45], "WARN", f"score={d.get('score')}")
        elif d.get("level") == "tfidf":
            record("DIRECT", q[:45], "WARN", f"tfidf score={d.get('score')}")
        else:
            record("DIRECT", q[:45], "FAIL", f"level={d.get('level')}")

    for q in ("tarif scol", "frais inscription", "comment register suptptic",
              "délai relevé notes", "attestation scolarité comment",
              "inscription supptic conditions", "calendrier exam"):
        d = _ask_api(q)
        if not d:
            record("TF-IDF", q[:40], "FAIL", "pas de réponse")
        elif d.get("level") == "tfidf":
            record("TF-IDF", q[:40], "OK", f"score={d.get('score')}")
        elif d.get("level") == "direct":
            record("TF-IDF", q[:40], "WARN", f"direct score={d.get('score')}")
        else:
            record("TF-IDF", q[:40], "FAIL", f"level={d.get('level')}")

    for q in ("Quel temps fait-il aujourd'hui ?", "Quelle est la capitale de la France ?",
              "Recette de crêpes", "Qui a gagné la CAN 2024 ?",
              "Comment hacker un wifi ?", "Prix du bitcoin aujourd'hui"):
        d = _ask_api(q)
        if d and d.get("level") == "offbase":
            record("OFFBASE", q[:40], "OK", f"score={d.get('score')}")
        else:
            record("OFFBASE", q[:40], "FAIL", f"level={d.get('level') if d else '?'}")

    d = _ask_api("C'est combien ??? !!! @#$")
    record("ROBUSTESSE", "Caractères spéciaux", "OK" if d and d.get("answer") else "FAIL")

    d = _ask_api("FRAIS SCOLARITÉ supptic")
    record("ROBUSTESSE", "Accents / casse", "OK" if d and d.get("level") in ("direct", "tfidf") else "WARN",
           f"level={d.get('level') if d else '?'}")


# ── API HTTP ─────────────────────────────────────────────────────────────────
def http_get(path: str, timeout: int = 30) -> tuple[int, str]:
    req = urllib.request.Request(f"{BASE_URL}{path}", method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read().decode("utf-8", errors="replace")


def http_post(path: str, body: dict | None = None, raw: bytes | None = None, timeout: int = 120) -> tuple[int, str, dict]:
    data = raw if raw is not None else json.dumps(body or {}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        text = resp.read().decode("utf-8", errors="replace")
        ct = resp.headers.get("Content-Type", "")
        return resp.status, text, {"content_type": ct}


def http_post_expect_error(path: str, body: dict | None = None, raw: bytes | None = None) -> tuple[int, str]:
    try:
        status, text, _ = http_post(path, body=body, raw=raw)
        return status, text
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def test_api():
    print("\n" + "=" * 60)
    print(f"  API HTTP — {BASE_URL}")
    print("=" * 60)

    # Server reachable?
    try:
        status, body = http_get("/api/chatbot/status/")
        data = json.loads(body)
        if data.get("pipeline", {}).get("ready"):
            record("API", "GET /api/chatbot/status/", "OK", "ready=true")
        else:
            record("API", "GET /api/chatbot/status/", "WARN", "ready=false")
    except Exception as e:
        record("API", "GET /api/chatbot/status/", "FAIL", str(e))
        record("API", "Suite API", "SKIP", "serveur inaccessible — lancez: python manage.py runserver")
        return

    try:
        status, body = http_get("/api/chatbot/reload-index/")
        data = json.loads(body)
        record("API", "GET /api/chatbot/reload-index/", "OK" if data.get("status") == "reloaded" else "FAIL", f"ntotal={data.get('ntotal')}")
    except Exception as e:
        record("API", "GET /api/chatbot/reload-index/", "FAIL", str(e))

    for path in ("/api/faq/", "/api/stats/"):
        try:
            status, _ = http_get(path)
            record("API", f"GET {path}", "OK" if status == 200 else "FAIL", f"HTTP {status}")
        except Exception as e:
            record("API", f"GET {path}", "FAIL", str(e))

    # Erreurs
    code, body = http_post_expect_error("/api/chatbot/ask/", {"question": "", "stream": False})
    record("API", "Question vide → 400", "OK" if code == 400 else "FAIL", f"HTTP {code}")

    code, body = http_post_expect_error("/api/chatbot/ask/", raw=b"pas du json")
    record("API", "JSON invalide → 400", "OK" if code == 400 else "FAIL", f"HTTP {code}")

    try:
        req = urllib.request.Request(f"{BASE_URL}/api/chatbot/ask/", method="GET")
        urllib.request.urlopen(req, timeout=10)
        record("API", "GET ask → 405", "FAIL", "devrait refuser GET")
    except urllib.error.HTTPError as e:
        record("API", "GET ask → 405", "OK" if e.code == 405 else "FAIL", f"HTTP {e.code}")

    # stream false — échantillon par niveau
    api_samples = [
        ("bonjour", "conv", "CONV"),
        ("Quels sont les frais de scolarité ?", "direct", "DIRECT"),
        ("tarif scol", "tfidf", "TF-IDF"),
        ("Quel temps fait-il ?", "offbase", "OFFBASE"),
    ]
    for question, exp_level, exp_method in api_samples:
        try:
            code, text, meta = http_post("/api/chatbot/ask/", {"question": question, "stream": False})
            data = json.loads(text)
            ok = data.get("level") == exp_level and data.get("method") == exp_method and data.get("answer")
            record("API-JSON", question[:35], "OK" if ok else "WARN",
                   f"level={data.get('level')} method={data.get('method')} score={data.get('score')}")
        except Exception as e:
            record("API-JSON", question[:35], "FAIL", str(e))

    # stream true — SSE
    try:
        code, text, meta = http_post("/api/chatbot/ask/", {"question": "bonjour", "stream": True})
        has_token = '"type": "token"' in text
        has_done = '"type": "done"' in text
        no_bug = "UnboundLocalError" not in text
        ok = has_token and has_done and no_bug and "text/event-stream" in meta.get("content_type", "")
        record("API-SSE", "POST ask stream=true", "OK" if ok else "FAIL",
               f"token={has_token} done={has_done} ct={meta.get('content_type','')[:30]}")
    except Exception as e:
        record("API-SSE", "POST ask stream=true", "FAIL", str(e))

    # history via API
    try:
        code, text, _ = http_post("/api/chatbot/ask/", {
            "question": "bonjour",
            "history": [{"role": "user", "content": "test"}],
            "stream": False,
        })
        data = json.loads(text)
        record("API", "history + stream=false", "OK" if data.get("level") == "conv" else "FAIL")
    except Exception as e:
        record("API", "history + stream=false", "FAIL", str(e))

    # test-llm (optionnel)
    try:
        code, text, _ = http_post("/api/chatbot/test-llm/", {"prompt": "Dis bonjour en une phrase."}, timeout=180)
        data = json.loads(text)
        if data.get("response"):
            record("API", "POST /api/chatbot/test-llm/", "OK", f"{data.get('llm_time_s')}s")
        else:
            record("API", "POST /api/chatbot/test-llm/", "WARN", data.get("error", "pas de réponse"))
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        record("API", "POST /api/chatbot/test-llm/", "WARN", f"HTTP {e.code}: {json.loads(err).get('error', err)[:80]}")
    except Exception as e:
        record("API", "POST /api/chatbot/test-llm/", "WARN", str(e)[:80])


def print_report():
    print("\n" + "=" * 60)
    print("  RAPPORT FINAL")
    print("=" * 60)
    counts = {"OK": 0, "FAIL": 0, "SKIP": 0, "WARN": 0}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1

    print(f"\n  ✔  OK    : {counts['OK']}")
    print(f"  ⚠  WARN  : {counts['WARN']}")
    print(f"  ✘  FAIL  : {counts['FAIL']}")
    print(f"  ⊘  SKIP  : {counts['SKIP']}")
    print(f"  Total   : {len(results)}")

    fails = [r for r in results if r.status == "FAIL"]
    if fails:
        print("\n  ── Échecs ──")
        for r in fails:
            print(f"  ✘  [{r.group}] {r.name} — {r.detail}")

    warns = [r for r in results if r.status == "WARN"]
    if warns:
        print("\n  ── Avertissements (non bloquants) ──")
        for r in warns[:15]:
            print(f"  ⚠  [{r.group}] {r.name} — {r.detail}")
        if len(warns) > 15:
            print(f"  … et {len(warns) - 15} autres")

    print("\n" + "=" * 60 + "\n")
    return counts["FAIL"]


def main():
    global BASE_URL
    if "--base-url" in sys.argv:
        i = sys.argv.index("--base-url")
        BASE_URL = sys.argv[i + 1].rstrip("/")

    t0 = time.time()
    print(f"\n  SUP'ONE — Suite de tests complète Gen3")
    print(f"  Base URL : {BASE_URL}\n")

    server_up = False
    try:
        urllib.request.urlopen(f"{BASE_URL}/api/chatbot/status/", timeout=15)
        server_up = True
        print("Serveur Django détecté — tests via API HTTP.\n")
    except Exception:
        print("Serveur Django non détecté — tests pipeline locaux.\n")

    if server_up:
        test_pipeline_via_api()
    else:
        print("Chargement pipeline local (FAISS + TF-IDF)…")
        try:
            setup_pipeline()
            test_pipeline()
        except OSError as e:
            record("SETUP", "Embedder / FAISS", "FAIL", str(e)[:100])
            print("\n  Lancez d'abord : python manage.py runserver\n")

    test_api()
    fails = print_report()
    print(f"Durée totale : {time.time() - t0:.1f}s")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()

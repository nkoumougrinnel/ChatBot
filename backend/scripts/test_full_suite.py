"""
Suite de tests : santé, questions types, feedback, cohérence des réponses.
Usage: python scripts/test_full_suite.py
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8001"

# (label, question, mots-clés attendus dans la réponse — au moins un)
QUESTIONS = [
    ("conv", "bonjour", ["bonjour", "aider", "SUP"]),
    ("conv", "merci", ["plaisir", "question"]),
    ("inscription", "Comment s'inscrire à SUP'PTIC ?", ["inscri", "SUP"]),
    ("localisation", "Où se trouve SUP'PTIC ?", ["SUP", "PTIC", "Cameroun", "Yaound", "Douala"]),
    ("frais", "Quels sont les frais de scolarité ?", ["frais", "scolar", "SUP", "paiement", "coût"]),
    ("stage", "Comment postuler à un stage ?", ["stage", "SUP", "candidat", "postul"]),
    ("club", "Comment rejoindre le Club Informatique ?", ["club", "informat", "SUP"]),
    ("horaires", "Quelles sont les heures d'ouverture ?", ["heure", "ouvert", "horair", "SUP"]),
    ("filiere", "Quelles filières propose SUP'PTIC ?", ["fili", "formation", "SUP", "cycle", "licence", "master", "informatique"]),
    ("hors_sujet", "Quelle est la capitale de la France ?", ["n'ai pas", "base", "secrétariat", "information"]),
]

OFFBASE_MARKERS = (
    "n'ai pas cette information",
    "n'ai pas trouvé",
    "reformulez",
    "secrétariat",
)


def get(path: str, timeout: int = 30):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return json.loads(r.read())


def post(path: str, data: dict, timeout: int = 120):
    req = urllib.request.Request(
        BASE + path,
        json.dumps(data).encode(),
        {"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read()), r.status


def ask_gen3(question: str) -> dict:
    body, _ = post("/api/v2/chatbot/ask/", {"question": question, "stream": False}, timeout=180)
    return body


def ask_phase1(question: str) -> dict:
    return post("/api/chatbot/ask/", {"question": question, "top_k": 1}, timeout=60)[0]


def coherent(answer: str, keywords: list[str], label: str) -> tuple[bool, str]:
    if not answer or len(answer.strip()) < 10:
        return False, "réponse vide"
    low = answer.lower()
    if label == "hors_sujet":
        if any(m in low for m in OFFBASE_MARKERS):
            return True, "refus attendu"
        if any(k in low for k in ("paris", "france est")):
            return False, "réponse hors-sujet non filtrée"
        return True, "ok"
    if any(kw.lower() in low for kw in keywords):
        return True, "mots-clés ok"
    return False, f"mots-clés manquants: {keywords[:4]}"


def main() -> int:
    failures = []
    print("=" * 72)
    print("SUITE DE TESTS SUP'ONE AI")
    print("=" * 72)

    try:
        h = get("/api/health/")
    except Exception as exc:
        print(f"[ERREUR] Backend inaccessible sur {BASE}: {exc}")
        print("Lancez: python manage.py runserver 127.0.0.1:8001")
        return 1

    faq_count = h.get("faq_count", "?")
    gen3 = h.get("gen3", {})
    print(f"Health: status={h.get('status')} | FAQ={faq_count} | Gen3={gen3.get('available')}")
    if h.get("phase1") == "indexing_required":
        print("[ATTENTION] Index Phase 1 incomplet — python manage.py rebuild_vectors")

    print("\n--- Questions Gen3 ---")
    for label, question, keywords in QUESTIONS:
        t0 = time.time()
        try:
            r = ask_gen3(question)
        except urllib.error.HTTPError as exc:
            failures.append((label, question, f"HTTP {exc.code}"))
            print(f"[FAIL] {label}: HTTP {exc.code}")
            continue
        except Exception as exc:
            failures.append((label, question, str(exc)))
            print(f"[FAIL] {label}: {exc}")
            continue

        dt = time.time() - t0
        ans = (r.get("answer") or "").strip()
        level = r.get("level", "?")
        score = r.get("score", 0)
        ok, note = coherent(ans, keywords, label)
        status = "OK" if ok else "INCOHERENT"
        if not ok:
            failures.append((label, question, note))
        preview = re.sub(r"\s+", " ", ans)[:120]
        print(f"[{status}] {label} ({dt:.1f}s) level={level} score={score:.3f} — {note}")
        print(f"       Q: {question[:60]}")
        print(f"       R: {preview}...")

    print("\n--- Feedback API ---")
    fb_questions = [
        ("positif", "Comment s'inscrire à SUP'PTIC ?", "positif"),
        ("negatif", "Quels sont les frais de scolarité ?", "negatif"),
    ]
    for fb_label, q, fb_type in fb_questions:
        try:
            payload = {
                "feedback_type": fb_type,
                "question_utilisateur": q,
                "comment": f"Test auto {fb_label}",
                "score_similarite": 0.85 if fb_type == "positif" else 0.4,
            }
            res, status = post("/api/feedback/", payload, timeout=30)
            if status in (200, 201):
                print(f"[OK] feedback {fb_type} — id={res.get('id', '?')}")
            else:
                failures.append(("feedback", q, f"status {status}"))
                print(f"[FAIL] feedback {fb_type} — status {status}")
        except Exception as exc:
            failures.append(("feedback", q, str(exc)))
            print(f"[FAIL] feedback {fb_type}: {exc}")

    print("\n--- Phase 1 (échantillon) ---")
    for label, question, keywords in QUESTIONS[:4]:
        try:
            r = ask_phase1(question)
            top = (r.get("results") or [{}])[0]
            score = float(top.get("score", 0) or 0)
            ans = top.get("answer", "")
            ok, note = coherent(ans, keywords, label)
            status = "OK" if ok else "INCOHERENT"
            if not ok:
                failures.append((f"p1-{label}", question, note))
            print(f"[{status}] p1-{label} score={score:.3f} — {note}")
        except Exception as exc:
            failures.append((f"p1-{label}", question, str(exc)))
            print(f"[FAIL] p1-{label}: {exc}")

    print("\n" + "=" * 72)
    if failures:
        print(f"ECHECS: {len(failures)}")
        for label, q, err in failures:
            print(f"  - {label}: {err} | {q[:50]}")
        return 1
    print("TOUS LES TESTS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

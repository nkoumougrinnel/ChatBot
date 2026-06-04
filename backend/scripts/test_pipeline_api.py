"""Test rapide du pipeline Gen3 via l'API REST."""
import json
import sys
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=30) as r:
        return json.loads(r.read())


def post(path, data):
    req = urllib.request.Request(
        BASE + path,
        json.dumps(data).encode(),
        {"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def main():
    ok = True

    print("=== 1. Health ===")
    h = get("/api/health/")
    print(
        "status:", h.get("status"),
        "| gen3:", h.get("gen3", {}).get("available"),
        "| llm:", h.get("gen3", {}).get("pipeline", {}).get("llm_available"),
    )

    print("\n=== 2. LLM Status ===")
    s = get("/api/v2/chatbot/status/")
    print("available:", s.get("available"), "| model:", s.get("model"))
    if s.get("error"):
        print("error:", s.get("error"))
        ok = False

    questions = [
        ("CONV", "bonjour"),
        ("FAISS", "Où se trouve SUP'PTIC ?"),
        ("LLM", "Quels sont les frais de scolarité à SUP'PTIC ?"),
    ]

    for label, q in questions:
        print(f"\n=== 3. Ask [{label}]: {q} ===")
        t0 = time.time()
        try:
            r = post("/api/v2/chatbot/ask/", {"question": q, "stream": False})
        except urllib.error.HTTPError as exc:
            print("HTTP error:", exc.read().decode())
            ok = False
            continue
        dt = time.time() - t0
        print(
            f"level: {r.get('level')} | method: {r.get('method')} | "
            f"score: {r.get('score')} | {dt:.1f}s"
        )
        ans = (r.get("answer") or "")[:220]
        print("answer:", ans.replace("\n", " "))

    print("\n=== RESULT:", "PIPELINE OK" if ok else "ISSUES DETECTED", "===")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

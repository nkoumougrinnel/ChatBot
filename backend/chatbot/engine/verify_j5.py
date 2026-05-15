"""
verify_j5.py — Vérifications Backend Jour 5 (roadmap Phase 2)

Vérifications effectuées :
    1. Test end-to-end : question → embed → FAISS → prompt → LLM → réponse
    2. Vérification que le LLM reste dans le contexte fourni (pas d'hallucination)

Usage :
    python verify_j5.py                   # vérification complète
    python verify_j5.py --no-llm          # sans LLM (si Ollama absent)
    python verify_j5.py --verbose         # affiche les prompts complets

Prérequis :
    - index.bin + metadata.json dans backend/rag_data/
    - Ollama lancé : ollama serve  (sauf si --no-llm)
    - Modèle phi3:mini installé   (sauf si --no-llm)
"""

import argparse
import sys
import time
from pathlib import Path

# ── Résolution des imports depuis n'importe quel répertoire courant ──────────
_ENGINE = Path(__file__).resolve().parent / "chatbot" / "engine"
_BACKEND_ROOT = Path(__file__).resolve().parents[2]  # backend/
for path in (_BACKEND_ROOT, _ENGINE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# ── Couleurs terminal ────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

OK   = f"{GREEN}  ✔{RESET}"
FAIL = f"{RED}  ✗{RESET}"
WARN = f"{YELLOW}  ⚠{RESET}"
INFO = f"{CYAN}  →{RESET}"


def header(title: str) -> None:
    print(f"\n{BOLD}{'─' * 60}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{BOLD}{'─' * 60}{RESET}")


def result(ok: bool, msg: str) -> None:
    print(f"{OK if ok else FAIL}  {msg}")


# ── Résultats globaux ────────────────────────────────────────────────────────
_results: list[tuple[bool, str]] = []


def check(ok: bool, label: str, detail: str = "") -> bool:
    _results.append((ok, label))
    result(ok, label)
    if detail:
        prefix = INFO if ok else WARN
        for line in detail.strip().splitlines():
            print(f"      {line}")
    return ok


# ════════════════════════════════════════════════════════════════════════════
# VÉRIFICATION 1 — Imports et modules disponibles
# ════════════════════════════════════════════════════════════════════════════
def check_imports() -> bool:
    header("1/4 — Vérification des modules engine/")
    ok_all = True

    modules = [
        ("embedder",       "encode, encode_batch"),
        ("faiss_search",   "load_index, search_with_metadata, is_loaded"),
        ("prompt_builder", "build_prompt, build_no_context_prompt"),
        ("llm_client",     "generate, generate_stream, check_availability"),
        ("rag_pipeline",   "ask, ask_stream"),
        ("tfidf_fallback", "load, search"),
    ]

    for mod_name, symbols in modules:
        try:
            mod = __import__(mod_name)
            missing = [s.strip() for s in symbols.split(",")
                       if not hasattr(mod, s.strip())]
            if missing:
                ok_all = check(False, f"{mod_name}.py chargé mais symboles manquants : {missing}")
            else:
                ok_all &= check(True, f"{mod_name}.py — OK ({symbols})")
        except ImportError as e:
            ok_all = check(False, f"{mod_name}.py — INTROUVABLE", str(e))
            ok_all = False

    return ok_all


# ════════════════════════════════════════════════════════════════════════════
# VÉRIFICATION 2 — Embedder (MiniLM)
# ════════════════════════════════════════════════════════════════════════════
def check_embedder() -> bool:
    import numpy as np
    from embedder import encode

    header("2/4 — Vérification embedder (MiniLM)")
    ok_all = True

    # Forme et dtype
    vec = encode("C'est combien pour s'inscrire ?")
    ok_all &= check(vec.shape == (384,), f"Forme du vecteur = {vec.shape}  (attendu : (384,))")
    ok_all &= check(vec.dtype == np.float32, f"dtype = {vec.dtype}  (attendu : float32)")

    # Normalisation
    norm = float(np.linalg.norm(vec))
    ok_all &= check(abs(norm - 1.0) < 1e-4, f"Norme = {norm:.6f}  (attendu ≈ 1.0)")

    # Similarité sémantique (le test clé Phase 2)
    pairs = [
        ("C'est combien pour s'inscrire ?", "Quels sont les frais de scolarité ?"),
        ("Comment rejoindre SUP'PTIC ?",    "Quelle est la procédure d'admission ?"),
    ]
    for q1, q2 in pairs:
        v1, v2 = encode(q1), encode(q2)
        sim = float(np.dot(v1, v2))
        ok_all &= check(
            sim > 0.70,
            f"Similarité cosinus = {sim:.4f}  (seuil > 0.70)",
            f"'{q1}'\n         vs '{q2}'"
        )

    # Latence
    t0 = time.time()
    for _ in range(5):
        encode("test de latence")
    ms = (time.time() - t0) / 5 * 1000
    ok_all &= check(ms < 200, f"Latence moyenne = {ms:.1f} ms  (objectif < 200 ms)")

    return ok_all


# ════════════════════════════════════════════════════════════════════════════
# VÉRIFICATION 3 — FAISS
# ════════════════════════════════════════════════════════════════════════════
def check_faiss() -> bool:
    from embedder import encode
    import faiss_search

    header("3/4 — Vérification index FAISS")
    ok_all = True

    # Chargement
    faiss_search.load_index()
    ok_all &= check(faiss_search.is_loaded(), "Index FAISS chargé en mémoire")

    if not faiss_search.is_loaded():
        check(False, "Impossible de continuer les tests FAISS — index absent",
              "Lancez : python scripts/build_index.py")
        return False

    stats = faiss_search.get_index_stats()
    ok_all &= check(stats["ntotal"] > 0, f"Vecteurs dans l'index : {stats['ntotal']}")
    ok_all &= check(stats["dim"] == 384, f"Dimension : {stats['dim']}  (attendu : 384)")

    # Top-3 sur 10 questions variées
    test_questions = [
        "C'est combien pour s'inscrire ?",
        "Quels sont les frais de scolarité ?",
        "Comment rejoindre le club informatique ?",
        "Quelles sont les filières disponibles ?",
        "Où se trouve l'école ?",
        "Comment contacter l'administration ?",
        "Quand commence l'année académique ?",
        "Comment obtenir une bourse ?",
        "Quels documents fournir pour s'inscrire ?",
        "Quel est le programme de formation en réseaux ?",
    ]

    pertinents = 0
    print(f"\n{INFO}  Test top-3 sur {len(test_questions)} questions :")
    for q in test_questions:
        vec = encode(q)
        results = faiss_search.search_with_metadata(vec, k=3)
        best = results[0]["score"] if results else 0.0
        pertinent = best > 0.30
        if pertinent:
            pertinents += 1
        sym = f"{GREEN}✔{RESET}" if pertinent else f"{RED}✗{RESET}"
        print(f"      {sym} score={best:.4f} | '{q[:50]}'")

    ratio = pertinents / len(test_questions)
    ok_all &= check(ratio >= 0.70,
                    f"Questions pertinentes (score > 0.30) : {pertinents}/{len(test_questions)} ({ratio:.0%})  (seuil ≥ 70%)")

    return ok_all


# ════════════════════════════════════════════════════════════════════════════
# VÉRIFICATION 4 — End-to-end + anti-hallucination
# ════════════════════════════════════════════════════════════════════════════
def check_end_to_end(verbose: bool = False) -> bool:
    from embedder import encode
    import faiss_search
    from prompt_builder import build_prompt, build_no_context_prompt
    import llm_client
    from rag_pipeline import ask

    header("4/4 — Test end-to-end (question → embed → FAISS → prompt → LLM → réponse)")
    ok_all = True

    # ── Vérification Ollama ───────────────────────────────────────────────
    print(f"\n{INFO}  Vérification Ollama...")
    status = llm_client.check_availability()
    ok_all &= check(status["available"],
                    f"Ollama disponible — modèle : {status['model']}",
                    status.get("error") or "")

    if not status["available"]:
        check(False, "Tests LLM ignorés — Ollama non disponible",
              "Lancez : ollama serve  puis  ollama pull phi3:mini")
        return False

    # ── Test end-to-end complet ───────────────────────────────────────────
    questions_test = [
        {
            "question": "Quels sont les frais de scolarité à SUP'PTIC ?",
            "methode_attendue": "RAG",
            "hors_domaine": False,
        },
        {
            "question": "Comment s'inscrire à SUP'PTIC ?",
            "methode_attendue": "RAG",
            "hors_domaine": False,
        },
        {
            "question": "Quel temps fait-il aujourd'hui à Yaoundé ?",
            "methode_attendue": "TF-IDF",
            "hors_domaine": True,
        },
    ]

    print(f"\n{INFO}  Pipeline complet sur {len(questions_test)} questions :\n")

    for tc in questions_test:
        q = tc["question"]
        print(f"  {BOLD}Q : « {q} »{RESET}")

        t0 = time.time()
        try:
            result_data = ask(q, history=None)
            elapsed = time.time() - t0
        except Exception as e:
            check(False, f"Exception lors de ask() : {e}")
            ok_all = False
            continue

        answer     = result_data.get("answer", "")
        method     = result_data.get("method", "?")
        best_score = result_data.get("best_score", 0.0)

        # Latence < 3s (objectif roadmap)
        ok_latence = elapsed < 3.0
        ok_all &= check(ok_latence,
                        f"Latence = {elapsed:.2f}s  (objectif < 3s)")

        # Réponse non vide
        ok_all &= check(len(answer.strip()) > 10,
                        f"Réponse non vide ({len(answer)} caractères)")

        # Méthode cohérente avec le score
        if tc["hors_domaine"]:
            ok_all &= check(best_score < 0.55,
                            f"Score FAISS = {best_score:.4f} < 0.55 → bascule TF-IDF correcte")
        else:
            ok_all &= check(best_score >= 0.30,
                            f"Score FAISS = {best_score:.4f}  (méthode : {method})")

        # ── Anti-hallucination ────────────────────────────────────────────
        # Si la question est hors domaine, la réponse doit contenir un message
        # d'indirection et NE PAS affirmer des faits inventés.
        if tc["hors_domaine"]:
            indirection_phrases = [
                "je n'ai pas",
                "je ne dispose pas",
                "cette information",
                "secrétariat",
                "contacter",
                "je ne suis pas",
                "hors de ma",
            ]
            answer_lower = answer.lower()
            has_indirection = any(p in answer_lower for p in indirection_phrases)
            ok_all &= check(
                has_indirection,
                "Anti-hallucination : le LLM indique l'absence d'info (hors domaine)",
                f"Réponse : « {answer[:120].strip()}... »"
            )
        else:
            # Pour une question en domaine, vérifier que la réponse ne contient
            # pas de formules typiques d'hallucination ("je suppose", "il est possible
            # que", "probablement") sans ancrage dans le contexte.
            hallucination_markers = [
                "je suppose",
                "il est possible que",
                "probablement",
                "je pense que",
                "selon mes connaissances générales",
            ]
            answer_lower = answer.lower()
            markers_found = [m for m in hallucination_markers if m in answer_lower]
            ok_all &= check(
                len(markers_found) == 0,
                "Anti-hallucination : aucun marqueur de spéculation détecté",
                f"Marqueurs trouvés : {markers_found}" if markers_found else ""
            )

        if verbose:
            print(f"\n      {CYAN}--- Réponse complète ---{RESET}")
            print(f"      {answer[:300]}")
            print(f"      {CYAN}--- Fin réponse ---{RESET}\n")
        else:
            print(f"  {INFO}  Réponse : « {answer[:100].strip()}... »")

        print()

    # ── Test avec historique (mémoire conversationnelle) ─────────────────
    print(f"\n{INFO}  Test mémoire conversationnelle (2 tours) :")
    history = [
        {"role": "user",      "content": "Quels sont les frais de scolarité ?"},
        {"role": "assistant", "content": "Les frais s'élèvent à 500 000 FCFA par an."},
    ]
    try:
        t0 = time.time()
        result_data = ask("Et pour les boursiers ?", history=history)
        elapsed = time.time() - t0
        answer = result_data.get("answer", "")
        ok_all &= check(len(answer.strip()) > 10,
                        f"Réponse avec historique reçue ({elapsed:.2f}s, {len(answer)} car.)")
        if verbose:
            print(f"      Réponse : « {answer[:200]} »")
    except Exception as e:
        ok_all = check(False, f"Exception avec historique : {e}")

    return ok_all


# ════════════════════════════════════════════════════════════════════════════
# RAPPORT FINAL
# ════════════════════════════════════════════════════════════════════════════
def print_summary() -> bool:
    total  = len(_results)
    passed = sum(1 for ok, _ in _results if ok)
    failed = total - passed

    print(f"\n{BOLD}{'═' * 60}{RESET}")
    print(f"{BOLD}  RAPPORT FINAL — Vérifications Backend Jour 5{RESET}")
    print(f"{BOLD}{'═' * 60}{RESET}")
    print(f"  Tests exécutés : {total}")
    print(f"  {GREEN}Réussis        : {passed}{RESET}")
    if failed:
        print(f"  {RED}Échoués        : {failed}{RESET}")
        print(f"\n  {RED}Vérifications en échec :{RESET}")
        for ok, label in _results:
            if not ok:
                print(f"  {FAIL}  {label}")

    if failed == 0:
        print(f"\n  {GREEN}{BOLD}✔ TOUS LES CRITÈRES DU JOUR 5 SONT VALIDÉS{RESET}")
        print(f"  {GREEN}  Pull Request backend → dev : prête à être soumise.{RESET}")
    else:
        print(f"\n  {RED}{BOLD}✗ {failed} vérification(s) à corriger avant la Pull Request.{RESET}")

    print(f"{BOLD}{'═' * 60}{RESET}\n")
    return failed == 0


# ════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ════════════════════════════════════════════════════════════════════════════
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Vérifications Backend Jour 5 — Roadmap Phase 2 SUP'ONE"
    )
    parser.add_argument("--no-llm",  action="store_true",
                        help="Ignorer les tests nécessitant Ollama")
    parser.add_argument("--verbose", action="store_true",
                        help="Afficher les réponses complètes du LLM")
    args = parser.parse_args()

    print(f"\n{BOLD}{'═' * 60}{RESET}")
    print(f"{BOLD}  verify_j5.py — Vérifications Backend Jour 5{RESET}")
    print(f"{BOLD}  Projet : ChatBot SUP'ONE Phase 2{RESET}")
    print(f"{BOLD}{'═' * 60}{RESET}")

    # Étape 1 — Imports
    if not check_imports():
        print(f"\n{RED}Arrêt : modules engine/ manquants. Corrigez les imports d'abord.{RESET}")
        sys.exit(1)

    # Étape 2 — Embedder
    check_embedder()

    # Étape 3 — FAISS
    check_faiss()

    # Étape 4 — End-to-end + anti-hallucination
    if args.no_llm:
        print(f"\n{WARN}  Tests LLM ignorés (--no-llm).")
        _results.append((None, "Tests LLM ignorés (--no-llm)"))
    else:
        check_end_to_end(verbose=args.verbose)

    # Rapport final
    ok = print_summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

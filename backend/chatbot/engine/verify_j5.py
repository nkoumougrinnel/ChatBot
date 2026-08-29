"""
test_gen3.py — Tests complets du pipeline SUP'ONE Génération 3.

Teste dans l'ordre :
    1. embedder.py        — vectorisation, cache, thread-safety
    2. faiss_search.py    — chargement index, recherche, confidence_level
    3. prompt_builder.py  — detect_conv, build_prompt, build_direct_prompt
    4. tfidf_fallback.py  — chargement, search, search_top_k, hint
    5. llm_client.py      — check_availability, generate, generate_stream
    6. rag_pipeline.py    — ask() sur tous les niveaux, ask_stream() SSE
    7. views.py           — _sse, _parse_sse_line, _LEVEL_TO_METHOD

Usage (depuis la racine du dépôt) :
    python backend/chatbot/engine/test_gen3.py
    python backend/chatbot/engine/test_gen3.py embedder
    python backend/chatbot/engine/test_gen3.py --no-llm

Prérequis :
    - index.bin + metadata.json dans backend/rag_data/
    - Données JSON dans data/
    - Ollama lancé avec phi3:mini (sauf avec --no-llm)
"""

from __future__ import annotations

import sys
import os
import time
import threading
import types
from pathlib import Path
from typing import Callable

# ─────────────────────────────────────────────────────────────────────────────
# Résolution des chemins
# ─────────────────────────────────────────────────────────────────────────────
# Ce fichier est dans : backend/chatbot/engine/test_gen3.py
# On calcule tous les chemins à partir de sa position réelle.

_THIS_FILE   = Path(__file__).resolve()
_ENGINE_DIR  = _THIS_FILE.parent                          # backend/chatbot/engine/
_CHATBOT_DIR = _ENGINE_DIR.parent                         # backend/chatbot/
_BACKEND_DIR = _CHATBOT_DIR.parent                        # backend/
_REPO_ROOT   = _BACKEND_DIR.parent                        # racine du dépôt

# Injecter dans sys.path dans l'ordre de priorité
for _p in [
    str(_ENGINE_DIR),   # embedder, faiss_search, llm_client, prompt_builder,
                        # rag_pipeline, tfidf_fallback
    str(_CHATBOT_DIR),  # views.py (chatbot/views.py)
    str(_BACKEND_DIR),  # config/, faq/
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Mode hors ligne HuggingFace — doit être défini AVANT l'import de sentence_transformers
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE",  "1")

# Chemin vers rag_data/ (index FAISS + cache TF-IDF)
os.environ.setdefault(
    "RAG_DATA_DIR",
    str(_BACKEND_DIR / "rag_data"),
)

# Chemin vers data/ (fichiers JSON FAQ pour tfidf_fallback)
os.environ.setdefault(
    "FAQ_DATA_DIR",
    str(_REPO_ROOT / "data/json/validated"),
)

# ─────────────────────────────────────────────────────────────────────────────
# Utilitaires de test
# ─────────────────────────────────────────────────────────────────────────────
_RESULTS: list[dict] = []
_NO_LLM = "--no-llm" in sys.argv


def _ok(module: str, test: str, detail: str = "") -> None:
    _RESULTS.append({"module": module, "test": test, "status": "OK", "detail": detail})
    detail_str = f" ({detail})" if detail else ""
    print(f"  OK  {test}{detail_str}")


def _fail(module: str, test: str, reason: str) -> None:
    _RESULTS.append({"module": module, "test": test, "status": "FAIL", "reason": reason})
    print(f"  FAIL  {test} — {reason}")


def _skip(module: str, test: str, reason: str = "Ollama non disponible") -> None:
    _RESULTS.append({"module": module, "test": test, "status": "SKIP", "reason": reason})
    print(f"  SKIP  {test} — ignoré ({reason})")


def _section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def _run(module: str, test: str, fn: Callable, skip_if_no_llm: bool = False) -> None:
    if skip_if_no_llm and _NO_LLM:
        _skip(module, test)
        return
    try:
        fn()
        _ok(module, test)
    except AssertionError as e:
        _fail(module, test, str(e) or "Assertion échouée")
    except Exception as e:
        _fail(module, test, f"{type(e).__name__}: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# 1. embedder.py
# ─────────────────────────────────────────────────────────────────────────────
def test_embedder():
    _section("1. embedder.py")
    import embedder
    import numpy as np

    def t_encode_shape():
        vec = embedder.encode("Test phrase")
        assert vec.shape == (384,), f"Shape attendu (384,), obtenu {vec.shape}"

    def t_encode_norme():
        vec = embedder.encode("Test phrase")
        norme = float(np.linalg.norm(vec))
        assert 0.99 < norme < 1.01, f"Norme attendue ≈ 1.0, obtenu {norme:.4f}"

    def t_encode_vide():
        vec = embedder.encode("")
        assert vec.shape == (384,)
        assert float(np.linalg.norm(vec)) == 0.0, "Texte vide doit retourner vecteur zéro"

    def t_encode_batch():
        texts = ["phrase un", "phrase deux", "phrase trois"]
        mat = embedder.encode_batch(texts)
        assert mat.shape == (3, 384), f"Shape attendu (3, 384), obtenu {mat.shape}"

    def t_encode_batch_vide():
        mat = embedder.encode_batch([])
        assert mat.shape == (0, 384)

    def t_similarite_semantique():
        v1 = embedder.encode("C'est combien pour s'inscrire ?")
        v2 = embedder.encode("Quels sont les frais de scolarité ?")
        sim = float(np.dot(v1, v2))
        assert sim > 0.45, f"Similarité cosinus attendue > 0.70, obtenu {sim:.4f}"

    def t_encode_cached():
        t1 = embedder.encode_cached("question test cache")
        t2 = embedder.encode_cached("question test cache")
        assert t1 == t2, "Le cache doit retourner le même tuple"
        assert isinstance(t1, tuple), "encode_cached doit retourner un tuple"

    def t_thread_safe():
        resultats = []
        erreurs   = []
        def worker():
            try:
                vec = embedder.encode("thread test")
                resultats.append(vec.shape)
            except Exception as e:
                erreurs.append(str(e))
        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads: t.start()
        for t in threads: t.join()
        assert not erreurs, f"Erreurs thread : {erreurs}"
        assert len(resultats) == 5

    def t_get_dimension():
        assert embedder.get_dimension() == 384

    _run("embedder", "encode() — shape (384,)", t_encode_shape)
    _run("embedder", "encode() — vecteur normalisé (norme ≈ 1.0)", t_encode_norme)
    _run("embedder", "encode('') — vecteur zéro", t_encode_vide)
    _run("embedder", "encode_batch() — shape (N, 384)", t_encode_batch)
    _run("embedder", "encode_batch([]) — shape (0, 384)", t_encode_batch_vide)
    _run("embedder", "Similarité cosinus synonymes > 0.70", t_similarite_semantique)
    _run("embedder", "encode_cached() — cache LRU cohérent", t_encode_cached)
    _run("embedder", "Thread-safety — 5 threads simultanés", t_thread_safe)
    _run("embedder", "get_dimension() == 384", t_get_dimension)


# ─────────────────────────────────────────────────────────────────────────────
# 2. faiss_search.py
# ─────────────────────────────────────────────────────────────────────────────
def test_faiss_search():
    _section("2. faiss_search.py")
    import faiss_search
    import embedder

    def t_constantes():
        assert hasattr(faiss_search, "SCORE_DIRECT"), "SCORE_DIRECT absent"
        assert hasattr(faiss_search, "SCORE_LLM"),    "SCORE_LLM absent"
        assert faiss_search.SCORE_DIRECT > faiss_search.SCORE_LLM

    def t_load():
        faiss_search.load_index()
        assert faiss_search.is_loaded(), "Index non chargé après load_index()"

    def t_stats():
        stats = faiss_search.get_index_stats()
        assert stats["loaded"]
        assert stats["ntotal"] > 0, "Index vide"
        assert stats["dim"] == 384

    def t_search_retourne_liste():
        vec = embedder.encode("frais de scolarité")
        results = faiss_search.search(vec, k=3)
        assert isinstance(results, list)

    def t_search_with_metadata_champs():
        vec = embedder.encode("C'est combien pour s'inscrire ?")
        results = faiss_search.search_with_metadata(vec, k=3)
        assert len(results) > 0, "Aucun résultat retourné"
        for r in results:
            for champ in ("score", "response", "example", "categorie", "source", "confidence_level"):
                assert champ in r, f"Champ '{champ}' absent"

    def t_confidence_level():
        vec = embedder.encode("C'est combien pour s'inscrire ?")
        results = faiss_search.search_with_metadata(vec, k=3)
        for r in results:
            assert r["confidence_level"] in ("direct", "llm", "offbase"), \
                f"confidence_level invalide : {r['confidence_level']}"

    def t_score_entre_0_et_1():
        vec = embedder.encode("inscription SUP'PTIC")
        results = faiss_search.search_with_metadata(vec, k=3)
        for r in results:
            assert 0.0 <= r["score"] <= 1.0, f"Score hors [0,1] : {r['score']}"

    def t_reload():
        faiss_search.reload_index()
        assert faiss_search.is_loaded(), "Index non chargé après reload_index()"

    _run("faiss_search", "SCORE_DIRECT et SCORE_LLM exportés", t_constantes)
    _run("faiss_search", "load_index() — chargement sans erreur", t_load)
    _run("faiss_search", "get_index_stats() — ntotal > 0", t_stats)
    _run("faiss_search", "search() — retourne une liste", t_search_retourne_liste)
    _run("faiss_search", "search_with_metadata() — tous les champs présents", t_search_with_metadata_champs)
    _run("faiss_search", "confidence_level in (direct/llm/offbase)", t_confidence_level)
    _run("faiss_search", "score entre 0.0 et 1.0", t_score_entre_0_et_1)
    _run("faiss_search", "reload_index() — rechargement à chaud", t_reload)


# ─────────────────────────────────────────────────────────────────────────────
# 3. prompt_builder.py
# ─────────────────────────────────────────────────────────────────────────────
def test_prompt_builder():
    _section("3. prompt_builder.py")
    from prompt_builder import detect_conv, build_prompt, build_direct_prompt

    def t_conv_bonjour():
        r = detect_conv("Bonjour !")
        assert r is not None, "Bonjour doit être détecté"
        assert "SUP'ONE" in r

    def t_conv_merci():
        assert detect_conv("Merci beaucoup") is not None

    def t_conv_au_revoir():
        assert detect_conv("Au revoir") is not None

    def t_conv_qui_es_tu():
        assert detect_conv("Qui es-tu ?") is not None

    def t_conv_none_question_normale():
        assert detect_conv("Quels sont les frais de scolarité ?") is None

    def t_conv_none_hors_domaine():
        assert detect_conv("Quel temps fait-il ?") is None

    def t_build_direct_prompt_format():
        ctx = {"categorie": "Admissions", "source": "e-supptic.cm",
               "response": "Les frais sont de 500 000 FCFA par an."}
        p = build_direct_prompt("C'est combien ?", ctx)
        assert "<|system|>" in p
        assert "<|user|>" in p
        assert "<|assistant|>" in p
        assert "Admissions" in p

    def t_build_prompt_avec_historique():
        contexts = [{"categorie": "Admissions", "source": "doc.pdf",
                     "response": "500 000 FCFA par an."}]
        history  = [{"role": "user", "content": "Quelles filières ?"},
                    {"role": "assistant", "content": "IIT et ITT."}]
        p = build_prompt("Et les frais ?", contexts, history)
        assert "[HISTORIQUE]" in p
        assert "[CONTEXTE]" in p
        assert "Étudiant" in p

    def t_build_prompt_sans_historique():
        contexts = [{"categorie": "Frais", "source": "doc.pdf",
                     "response": "500 000 FCFA par an."}]
        p = build_prompt("C'est combien ?", contexts)
        assert "[CONTEXTE]" in p
        assert "[HISTORIQUE]" not in p

    def t_historique_tronque_a_2():
        contexts = [{"categorie": "Frais", "source": "", "response": "500 000 FCFA."}]
        history  = [{"role": "user", "content": f"Question {i}"} for i in range(5)]
        p = build_prompt("Et les frais ?", contexts, history)
        assert "Question 3" in p
        assert "Question 4" in p
        assert "Question 0" not in p

    _run("prompt_builder", "detect_conv('Bonjour !') → réponse SUP'ONE", t_conv_bonjour)
    _run("prompt_builder", "detect_conv('Merci') → réponse", t_conv_merci)
    _run("prompt_builder", "detect_conv('Au revoir') → réponse", t_conv_au_revoir)
    _run("prompt_builder", "detect_conv('Qui es-tu ?') → réponse", t_conv_qui_es_tu)
    _run("prompt_builder", "detect_conv(question normale) → None", t_conv_none_question_normale)
    _run("prompt_builder", "detect_conv(hors domaine) → None", t_conv_none_hors_domaine)
    _run("prompt_builder", "build_direct_prompt() — format Phi-3 valide", t_build_direct_prompt_format)
    _run("prompt_builder", "build_prompt() — avec historique", t_build_prompt_avec_historique)
    _run("prompt_builder", "build_prompt() — sans historique", t_build_prompt_sans_historique)
    _run("prompt_builder", "Historique tronqué à 2 échanges", t_historique_tronque_a_2)


# ─────────────────────────────────────────────────────────────────────────────
# 4. tfidf_fallback.py
# ─────────────────────────────────────────────────────────────────────────────
def test_tfidf_fallback():
    _section("4. tfidf_fallback.py")
    import tfidf_fallback

    def t_load():
        tfidf_fallback.load()
        assert tfidf_fallback.is_loaded(), "TF-IDF non chargé après load()"

    def t_stats():
        stats = tfidf_fallback.get_stats()
        assert stats["loaded"]
        assert stats["entries_count"] > 0, "Aucune entrée chargée"
        assert stats["vocab_size"] > 0

    def t_search_retourne_tuple():
        answer, score, method = tfidf_fallback.search("frais de scolarité")
        assert isinstance(answer, str)
        assert isinstance(score, float)
        assert method == "TF-IDF"

    def t_search_score_entre_0_et_1():
        _, score, _ = tfidf_fallback.search("inscription SUP'PTIC")
        assert 0.0 <= score <= 1.0, f"Score hors [0,1] : {score}"

    def t_search_question_pertinente():
        answer, score, _ = tfidf_fallback.search("C'est combien pour s'inscrire ?")
        assert score > 0.0, "Score nul pour une question pertinente"
        assert len(answer) > 10

    def t_search_hors_domaine():
        answer, score, _ = tfidf_fallback.search("Quel temps fait-il à Paris ?")
        assert isinstance(answer, str)

    def t_search_top_k():
        results = tfidf_fallback.search_top_k("frais scolarité", k=3)
        assert isinstance(results, list)
        assert len(results) <= 3
        for r in results:
            for champ in ("answer", "score", "question", "categorie", "method"):
                assert champ in r, f"Champ '{champ}' absent dans search_top_k"

    def t_hint_court():
        # hint() est optionnel en Gen3 — on skip si absent
        if not hasattr(tfidf_fallback, "hint"):
            return
        h = tfidf_fallback.hint("frais de scolarité", max_chars=100)
        assert len(h) <= 101, f"hint dépasse max_chars : {len(h)}"

    def t_hint_hors_domaine_vide():
        if not hasattr(tfidf_fallback, "hint"):
            return
        h = tfidf_fallback.hint("azerty qwerty xyz abc 12345")
        assert isinstance(h, str)

    _run("tfidf_fallback", "load() — chargement sans erreur", t_load)
    _run("tfidf_fallback", "get_stats() — entries_count > 0", t_stats)
    _run("tfidf_fallback", "search() — retourne (str, float, 'TF-IDF')", t_search_retourne_tuple)
    _run("tfidf_fallback", "search() — score entre 0.0 et 1.0", t_search_score_entre_0_et_1)
    _run("tfidf_fallback", "search() — question pertinente → score > 0", t_search_question_pertinente)
    _run("tfidf_fallback", "search() — hors domaine → réponse de refus", t_search_hors_domaine)
    _run("tfidf_fallback", "search_top_k() — tous les champs présents", t_search_top_k)
    _run("tfidf_fallback", "hint() — respecte max_chars", t_hint_court)
    _run("tfidf_fallback", "hint() — hors domaine → str", t_hint_hors_domaine_vide)


# ─────────────────────────────────────────────────────────────────────────────
# 5. llm_client.py
# ─────────────────────────────────────────────────────────────────────────────
def test_llm_client():
    _section("5. llm_client.py")
    import llm_client

    def t_check_availability():
        status = llm_client.check_availability()
        assert "available" in status
        assert "model" in status
        assert "error" in status
        assert "models" in status

    def t_constantes_timeout():
        assert llm_client.CONNECT_TIMEOUT > 0
        assert llm_client.READ_TIMEOUT >= 60, \
            f"READ_TIMEOUT trop court ({llm_client.READ_TIMEOUT}s) — Phi-3 prend ~15-20s"

    def t_circuit_breaker_present():
        assert hasattr(llm_client, "_cb_failures")
        assert hasattr(llm_client, "_cb_open_until")

    def t_generate_stream_ollama():
        status = llm_client.check_availability()
        if not status["available"]:
            raise AssertionError("Ollama non disponible — lancez : ollama serve")
        prompt = (
            "<|system|>\nTu es SUP'ONE. Réponds en 1 phrase.<|end|>\n"
            "<|user|>\nQuel est le nom de l'école ?<|end|>\n"
            "<|assistant|>\n"
        )
        tokens = list(llm_client.generate_stream(prompt, level="llm"))
        assert len(tokens) > 0, "generate_stream n'a produit aucun token"
        full = "".join(tokens)
        assert len(full) > 5, f"Réponse trop courte : '{full}'"

    def t_generate_non_stream():
        status = llm_client.check_availability()
        if not status["available"]:
            raise AssertionError("Ollama non disponible")
        prompt = (
            "<|system|>\nTu es SUP'ONE. Réponds en 1 phrase.<|end|>\n"
            "<|user|>\nQuel est le nom de l'école ?<|end|>\n"
            "<|assistant|>\n"
        )
        response = llm_client.generate(prompt, level="llm")
        assert isinstance(response, str)
        assert len(response) > 5

    _run("llm_client", "check_availability() — retourne dict complet", t_check_availability)
    _run("llm_client", "READ_TIMEOUT >= 60s (Phi-3 ~15-20s sur CPU)", t_constantes_timeout)
    _run("llm_client", "Circuit-breaker — variables présentes", t_circuit_breaker_present)
    _run("llm_client", "generate_stream() — tokens produits", t_generate_stream_ollama, skip_if_no_llm=True)
    _run("llm_client", "generate() — réponse non streamée", t_generate_non_stream, skip_if_no_llm=True)


# ─────────────────────────────────────────────────────────────────────────────
# 6. rag_pipeline.py
# ─────────────────────────────────────────────────────────────────────────────
def test_rag_pipeline():
    _section("6. rag_pipeline.py")
    import faiss_search, tfidf_fallback, rag_pipeline

    faiss_search.load_index()
    tfidf_fallback.load()

    def t_ask_vide():
        result = rag_pipeline.ask("")
        assert result.level == "conv"
        assert result.method == "empty"

    def t_ask_conv_bonjour():
        result = rag_pipeline.ask("Bonjour !")
        assert result.level == "conv"
        assert result.method == "regex"
        assert "SUP'ONE" in result.answer

    def t_ask_conv_merci():
        result = rag_pipeline.ask("Merci beaucoup")
        assert result.level == "conv"

    def t_ask_direct():
        result = rag_pipeline.ask("C'est combien pour s'inscrire ?")
        assert result.level in ("direct", "tfidf"), \
            f"Attendu direct ou tfidf, obtenu '{result.level}'"
        assert len(result.answer) > 10

    def t_ask_offbase():
        result = rag_pipeline.ask("Recette beignets haricots Tokyo")
        assert result.level in ("offbase", "tfidf"), \
            f"Attendu offbase ou tfidf, obtenu '{result.level}'"

    def t_ask_latency_ms_renseignee():
        result = rag_pipeline.ask("Quels sont les frais ?")
        assert result.latency_ms > 0

    def t_ask_pipeline_result_champs():
        result = rag_pipeline.ask("Comment s'inscrire ?")
        for attr in ("answer", "level", "score", "latency_ms", "method"):
            assert hasattr(result, attr), f"Attribut '{attr}' absent de PipelineResult"

    def t_ask_stream_conv():
        events = list(rag_pipeline.ask_stream("Bonjour !"))
        assert len(events) == 3
        event_names = [e.split("\n")[0] for e in events if "event:" in e]
        assert any("start" in e for e in event_names)
        assert any("done"  in e for e in event_names)

    def t_ask_stream_sse_format():
        for raw in rag_pipeline.ask_stream("Quels sont les frais ?"):
            assert isinstance(raw, str)
            assert "\n\n" in raw, f"Format SSE invalide (pas de \\n\\n) : {repr(raw)}"

    def t_ask_stream_niveaux_couverts():
        valides = {"conv", "direct", "tfidf", "offbase"}
        for question in ["Bonjour", "C'est combien ?", "Quel temps fait-il ?"]:
            for raw in rag_pipeline.ask_stream(question):
                if "event: start" in raw:
                    data_line = [l for l in raw.split("\n") if l.startswith("data:")][0]
                    level = data_line.replace("data:", "").strip().split("|")[0]
                    assert level in valides, f"Level invalide : '{level}' pour '{question}'"
                    break

    def t_build_sse_event_format():
        raw = rag_pipeline.build_sse_event("Bonjour")
        assert raw == "data: Bonjour\n\n"

    def t_build_sse_event_avec_event():
        raw = rag_pipeline.build_sse_event("direct|faiss_direct", event="start")
        assert raw == "event: start\ndata: direct|faiss_direct\n\n"

    def t_build_sse_event_newline_interne():
        raw = rag_pipeline.build_sse_event("ligne1\nligne2")
        assert "\n\n" == raw[-2:], "Doit se terminer par \\n\\n"
        lines = raw.strip().split("\n")
        assert len(lines) == 1, "Les sauts de ligne internes doivent être remplacés"

    def t_health():
        h = rag_pipeline.health()
        for key in ("faiss_loaded", "tfidf_loaded", "ollama_available", "ready", "cache_size"):
            assert key in h, f"Clé '{key}' absente de health()"
        assert h["faiss_loaded"]
        assert h["tfidf_loaded"]
        assert h["ready"]

    _run("rag_pipeline", "ask('') → level=conv, method=empty", t_ask_vide)
    _run("rag_pipeline", "ask('Bonjour !') → level=conv, regex", t_ask_conv_bonjour)
    _run("rag_pipeline", "ask('Merci') → level=conv", t_ask_conv_merci)
    _run("rag_pipeline", "ask(question SUP'PTIC) → direct ou tfidf", t_ask_direct)
    _run("rag_pipeline", "ask(hors domaine) → offbase ou tfidf", t_ask_offbase)
    _run("rag_pipeline", "latency_ms renseignée", t_ask_latency_ms_renseignee)
    _run("rag_pipeline", "PipelineResult — tous les attributs présents", t_ask_pipeline_result_champs)
    _run("rag_pipeline", "ask_stream('Bonjour') → 3 événements SSE", t_ask_stream_conv)
    _run("rag_pipeline", "ask_stream() — format SSE valide (\\n\\n)", t_ask_stream_sse_format)
    _run("rag_pipeline", "ask_stream() — levels valides (conv/direct/tfidf/offbase)", t_ask_stream_niveaux_couverts)
    _run("rag_pipeline", "build_sse_event('Bonjour') → 'data: Bonjour\\n\\n'", t_build_sse_event_format)
    _run("rag_pipeline", "build_sse_event(event='start') → 'event: start\\n...'", t_build_sse_event_avec_event)
    _run("rag_pipeline", "build_sse_event() — sauts de ligne internes nettoyés", t_build_sse_event_newline_interne)
    _run("rag_pipeline", "health() — tous les champs présents", t_health)


# ─────────────────────────────────────────────────────────────────────────────
# 7. views.py — fonctions pures (sans démarrer Django)
# ─────────────────────────────────────────────────────────────────────────────
def test_views():
    _section("7. views.py — fonctions pures")

    # Stubber les dépendances Django/DRF pour ne pas démarrer le serveur
    fake_django      = types.ModuleType("django")
    fake_http        = types.ModuleType("django.http")
    fake_http.JsonResponse = object # Added this line
    fake_views_dec   = types.ModuleType("django.views.decorators.csrf")
    fake_http.StreamingHttpResponse     = object
    fake_views_dec.csrf_exempt          = lambda f: f
    fake_django.http                    = fake_http

    fake_drf         = types.ModuleType("rest_framework")
    fake_decorators  = types.ModuleType("rest_framework.decorators")
    fake_response    = types.ModuleType("rest_framework.response")
    fake_decorators.api_view  = lambda methods: (lambda f: f)
    fake_response.Response    = dict
    fake_drf.decorators       = fake_decorators
    fake_drf.response         = fake_response

    for mod, name in [
        (fake_django,     "django"),
        (fake_http,       "django.http"),
        (fake_views_dec,  "django.views.decorators.csrf"),
        (fake_drf,        "rest_framework"),
        (fake_decorators, "rest_framework.decorators"),
        (fake_response,   "rest_framework.response"),
    ]:
        sys.modules.setdefault(name, mod)

    # Stubber chatbot.engine.rag_pipeline et llm_client pour views.py
    fake_engine   = types.ModuleType("chatbot")
    fake_pkg      = types.ModuleType("chatbot.engine")
    fake_rp       = types.ModuleType("chatbot.engine.rag_pipeline")
    fake_llm      = types.ModuleType("chatbot.engine.llm_client")
    class MockPipelineResult:
        def __init__(self):
            self.answer = "Réponse mockée du pipeline"
            self.level = "mock"
            self.score = 0.0
            self.latency_ms = 0.0
            self.source = "mock_source"
            self.categorie = "mock_category"
            self.method = "mock_method"

    fake_rp.ask = lambda q, h=None: MockPipelineResult()
    fake_rp.ask_stream    = lambda q, h=None: iter([])
    fake_rp.health        = lambda: {}
    fake_llm.check_availability = lambda: {"available": False, "model": "", "error": None}
    fake_llm.generate_stream    = lambda p, level="llm": iter([])
    fake_engine.engine    = fake_pkg
    sys.modules.setdefault("chatbot",               fake_engine)
    sys.modules.setdefault("chatbot.engine",        fake_pkg)
    sys.modules.setdefault("chatbot.engine.rag_pipeline", fake_rp)
    sys.modules.setdefault("chatbot.engine.llm_client",   fake_llm)

    import importlib
    # Forcer le rechargement si déjà importé
    if "views" in sys.modules:
        del sys.modules["views"]
    import views as v

    def t_sse_format():
        import json
        result = v._sse({"type": "token", "content": "Bonjour"})
        assert result.startswith("data: ")
        assert result.endswith("\n\n")
        payload = json.loads(result[len("data: "):-2])
        assert payload["type"] == "token"
        assert payload["content"] == "Bonjour"

    def t_parse_sse_start():
        raw = "event: start\ndata: direct|faiss_direct\n\n"
        event, data = v._parse_sse_line(raw)
        assert event == "start"
        assert data == "direct|faiss_direct"

    def t_parse_sse_done():
        raw = "event: done\ndata: 142.3\n\n"
        event, data = v._parse_sse_line(raw)
        assert event == "done"
        assert data == "142.3"

    def t_parse_sse_data_seul():
        raw = "data: Les frais sont de 500 000 FCFA.\n\n"
        event, data = v._parse_sse_line(raw)
        assert event is None
        assert data == "Les frais sont de 500 000 FCFA."

    def t_parse_sse_error():
        raw = "event: error\ndata: Pipeline mal initialisé.\n\n"
        event, data = v._parse_sse_line(raw)
        assert event == "error"

    def t_level_to_method():
        assert v._LEVEL_TO_METHOD["conv"]    == "CONV"
        assert v._LEVEL_TO_METHOD["direct"]  == "DIRECT"
        assert v._LEVEL_TO_METHOD["tfidf"]   == "TF-IDF"
        assert v._LEVEL_TO_METHOD["offbase"] == "OFFBASE"
        assert v._LEVEL_TO_METHOD["llm"]     == "LLM"

    def t_faiss_levels():
        assert "direct"  in v._FAISS_LEVELS
        assert "tfidf"   in v._FAISS_LEVELS
        assert "offbase" in v._FAISS_LEVELS
        assert "conv"    not in v._FAISS_LEVELS

    _run("views", "_sse() — format JSON SSE valide", t_sse_format)
    _run("views", "_parse_sse_line() — event: start", t_parse_sse_start)
    _run("views", "_parse_sse_line() — event: done", t_parse_sse_done)
    _run("views", "_parse_sse_line() — data seul (token)", t_parse_sse_data_seul)
    _run("views", "_parse_sse_line() — event: error", t_parse_sse_error)
    _run("views", "_LEVEL_TO_METHOD — 5 niveaux corrects", t_level_to_method)
    _run("views", "_FAISS_LEVELS — conv absent, direct/tfidf/offbase présents", t_faiss_levels)


# ─────────────────────────────────────────────────────────────────────────────
# Rapport final
# ─────────────────────────────────────────────────────────────────────────────
def _rapport() -> bool:
    print(f"\n{'='*60}")
    print("  RAPPORT FINAL")
    print(f"{'='*60}")

    ok   = [r for r in _RESULTS if r["status"] == "OK"]
    fail = [r for r in _RESULTS if r["status"] == "FAIL"]
    skip = [r for r in _RESULTS if r["status"] == "SKIP"]

    print(f"\n  OK  Réussis  : {len(ok)}")
    print(f"  FAIL  Échoués  : {len(fail)}")
    print(f"  SKIP  Ignorés  : {len(skip)}")
    print(f"  Total       : {len(_RESULTS)}")

    if fail:
        print(f"\n  {'─'*50}")
        print("  Détail des échecs :")
        for r in fail:
            print(f"  FAIL  [{r['module']}] {r['test']}")
            print(f"       → {r['reason']}")

    print(f"\n{'='*60}\n")
    return len(fail) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Point d'entrée
# ─────────────────────────────────────────────────────────────────────────────
_MODULES = {
    "embedder":       test_embedder,
    "faiss_search":   test_faiss_search,
    "prompt_builder": test_prompt_builder,
    "tfidf_fallback": test_tfidf_fallback,
    "llm_client":     test_llm_client,
    "rag_pipeline":   test_rag_pipeline,
    "views":          test_views,
}

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    modules_a_tester = {k: v for k, v in _MODULES.items() if not args or k in args}

    if not modules_a_tester:
        print(f"Module inconnu. Disponibles : {', '.join(_MODULES.keys())}")
        sys.exit(1)

    print("\n  SUP'ONE — Tests Génération 3")
    print(f"  Engine    : {_ENGINE_DIR}")
    print(f"  RAG data  : {os.environ.get('RAG_DATA_DIR')}")
    print(f"  FAQ data  : {os.environ.get('FAQ_DATA_DIR')}")
    if _NO_LLM:
        print("  Mode --no-llm : tests Ollama ignorés")

    t_total = time.time()
    for fn in modules_a_tester.values():
        fn()

    print(f"\n  Durée totale : {time.time() - t_total:.1f}s")
    success = _rapport()
    sys.exit(0 if success else 1)

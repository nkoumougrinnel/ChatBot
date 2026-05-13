"""
test_fallback.py — Tests unitaires pour tfidf_fallback.py.

Exécution depuis Django :
    python manage.py test chatbot.tests.test_fallback

Exécution standalone :
    python backend/chatbot/tests/test_fallback.py
"""

import os
import sys
import unittest
from pathlib import Path

# --- Résolution du sys.path ---
_THIS_DIR = Path(__file__).resolve().parent
_ENGINE   = _THIS_DIR.parent / "engine"
_BACKEND  = _THIS_DIR.parent.parent

for _p in [str(_ENGINE), str(_BACKEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE",  "1")

import tfidf_fallback


class TestTfidfFallback(unittest.TestCase):
    """Tests unitaires pour tfidf_fallback.py."""

    @classmethod
    def setUpClass(cls):
        """Charge le moteur TF-IDF une seule fois."""
        tfidf_fallback.load()
        cls._loaded = tfidf_fallback.is_loaded()

    def _skip_if_not_loaded(self):
        if not self._loaded:
            self.skipTest("Moteur TF-IDF non chargé (données absentes).")

    # ── Tests de base ────────────────────────────────────────────────

    def test_is_loaded(self):
        """Le moteur TF-IDF doit pouvoir être chargé."""
        self._skip_if_not_loaded()
        self.assertTrue(tfidf_fallback.is_loaded())

    def test_search_returns_tuple(self):
        """search() doit retourner un tuple de 3 éléments."""
        self._skip_if_not_loaded()
        result = tfidf_fallback.search("Quels sont les frais de scolarité ?")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)

    def test_search_method_is_tfidf(self):
        """Le champ méthode doit toujours valoir 'TF-IDF'."""
        self._skip_if_not_loaded()
        _, _, method = tfidf_fallback.search("inscription SUP'PTIC")
        self.assertEqual(method, "TF-IDF")

    def test_search_score_between_0_and_1(self):
        """Le score retourné doit être entre 0 et 1."""
        self._skip_if_not_loaded()
        _, score, _ = tfidf_fallback.search("frais de scolarité")
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_search_answer_is_string(self):
        """La réponse retournée doit être une chaîne non vide."""
        self._skip_if_not_loaded()
        answer, _, _ = tfidf_fallback.search("frais de scolarité")
        self.assertIsInstance(answer, str)
        self.assertGreater(len(answer.strip()), 0)

    # ── Test bascule automatique (cœur du J9) ────────────────────────

    def test_out_of_domain_questions_low_score(self):
        """
        Les questions hors domaine doivent avoir un score TF-IDF < 0.50.
        Ce score < 0.55 déclenche la bascule TF-IDF dans rag_pipeline.
        """
        self._skip_if_not_loaded()

        out_of_domain = [
            "Quel temps fait-il aujourd'hui à Paris ?",
            "Quelle est la recette de la tarte aux pommes ?",
            "Qui a gagné la Coupe du monde 2022 ?",
            "Comment programmer en Rust ?",
        ]

        for question in out_of_domain:
            answer, score, method = tfidf_fallback.search(question)
            self.assertEqual(method, "TF-IDF")
            self.assertIsInstance(answer, str)
            self.assertLess(
                score, 0.50,
                f"Score TF-IDF trop élevé pour une question hors domaine : "
                f"'{question}' → score={score:.4f}"
            )

    def test_in_domain_questions_have_answers(self):
        """Les questions SUP'PTIC doivent retourner une vraie réponse."""
        self._skip_if_not_loaded()

        in_domain = [
            "Quels sont les frais de scolarité ?",
            "Comment s'inscrire à SUP'PTIC ?",
        ]

        for question in in_domain:
            answer, score, _ = tfidf_fallback.search(question)
            if score > 0.05:
                self.assertNotIn(
                    "Je n'ai pas cette information",
                    answer,
                    f"Question en domaine sans réponse : '{question}' (score={score:.4f})"
                )

    def test_fallback_interface_for_rag_pipeline(self):
        """
        Vérifie l'interface exacte attendue par rag_pipeline.py :
        search() → (str, float, str).
        """
        self._skip_if_not_loaded()
        answer, score, method = tfidf_fallback.search("Quel temps fait-il ?")
        self.assertIsInstance(answer, str)
        self.assertIsInstance(score,  float)
        self.assertEqual(method, "TF-IDF")
        self.assertGreater(len(answer), 0)

    # ── Tests search_top_k ────────────────────────────────────────────

    def test_search_top_k_structure(self):
        """search_top_k() doit retourner des dicts avec les bons champs."""
        self._skip_if_not_loaded()
        results  = tfidf_fallback.search_top_k("frais scolarité", k=3)
        required = {"answer", "score", "question", "categorie", "method"}
        for r in results:
            missing = required - set(r.keys())
            self.assertEqual(len(missing), 0, f"Champs manquants : {missing}")

    def test_search_top_k_sorted(self):
        """search_top_k() doit retourner les résultats triés par score décroissant."""
        self._skip_if_not_loaded()
        results = tfidf_fallback.search_top_k("inscription", k=5)
        if len(results) < 2:
            return
        scores = [r["score"] for r in results]
        for i in range(len(scores) - 1):
            self.assertGreaterEqual(scores[i], scores[i + 1])

    # ── Tests de robustesse ───────────────────────────────────────────

    def test_search_empty_query(self):
        """search() avec une chaîne vide ne doit pas lever d'exception."""
        self._skip_if_not_loaded()
        try:
            answer, score, method = tfidf_fallback.search("")
            self.assertIsInstance(answer, str)
        except Exception as e:
            self.fail(f"Exception avec chaîne vide : {e}")

    def test_search_special_characters(self):
        """search() avec des caractères spéciaux ne doit pas lever d'exception."""
        self._skip_if_not_loaded()
        try:
            answer, score, method = tfidf_fallback.search("!@#$%^&*()")
            self.assertIsInstance(answer, str)
        except Exception as e:
            self.fail(f"Exception avec caractères spéciaux : {e}")

    def test_get_stats_structure(self):
        """get_stats() doit retourner un dict avec les bonnes clés."""
        stats = tfidf_fallback.get_stats()
        self.assertIn("loaded",         stats)
        self.assertIn("entries_count",  stats)
        self.assertIn("vocab_size",     stats)
        if self._loaded:
            self.assertTrue(stats["loaded"])
            self.assertGreater(stats["entries_count"], 0)
            self.assertGreater(stats["vocab_size"],     0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

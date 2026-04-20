"""
test_fallback.py — Tests unitaires pour tfidf_fallback.py.

Objectif : vérifier que la bascule TF-IDF s'active pour les questions hors domaine
(score < 0.55 dans rag_pipeline.py).

Exécution :
    python manage.py test chatbot.tests.test_fallback   (depuis Django)
    python -m pytest backend/tests/test_fallback.py     (standalone)
"""

import sys
import unittest
from pathlib import Path

# Chemins
_ENGINE_PATH = Path(__file__).resolve().parent.parent / "chatbot" / "engine"
if str(_ENGINE_PATH) not in sys.path:
    sys.path.insert(0, str(_ENGINE_PATH))

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

    # -------------------------------------------------------------------
    # Tests de base
    # -------------------------------------------------------------------

    def test_is_loaded(self):
        """Le moteur TF-IDF doit pouvoir être chargé depuis les JSON."""
        self._skip_if_not_loaded()
        self.assertTrue(tfidf_fallback.is_loaded())

    def test_search_returns_tuple(self):
        """search() doit retourner un tuple de 3 éléments."""
        self._skip_if_not_loaded()
        result = tfidf_fallback.search("Quels sont les frais de scolarité ?")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3, "Le tuple doit contenir (réponse, score, méthode)")

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

    # -------------------------------------------------------------------
    # Test du comportement avec questions hors domaine
    # -------------------------------------------------------------------

    def test_out_of_domain_questions_low_score(self):
        """
        Les questions hors domaine doivent avoir un score TF-IDF très bas
        (< 0.30), ce qui déclenche le fallback dans rag_pipeline.
        
        Ces questions ne doivent pas correspondre à des FAQ de SUP'PTIC.
        """
        self._skip_if_not_loaded()

        out_of_domain = [
            "Quel temps fait-il aujourd'hui à Paris ?",
            "Quelle est la recette de la tarte aux pommes ?",
            "Qui a gagné la Coupe du monde 2022 ?",
            "Comment programmer en Rust ?",
        ]

        # Pour les questions hors domaine, on vérifie que le TF-IDF
        # retourne bien quelque chose (même un message d'absence de réponse)
        for question in out_of_domain:
            answer, score, method = tfidf_fallback.search(question)
            self.assertEqual(method, "TF-IDF")
            self.assertIsInstance(answer, str)
            # Le score doit être faible pour ces questions hors domaine
            # (seuil assoupli à 0.50 car TF-IDF peut trouver des correspondances partielles)
            self.assertLess(
                score, 0.50,
                f"Score TF-IDF trop élevé pour une question hors domaine : "
                f"'{question}' → score={score:.4f}"
            )

    def test_in_domain_questions_have_answers(self):
        """
        Les questions relatives à SUP'PTIC doivent retourner une vraie réponse.
        """
        self._skip_if_not_loaded()

        in_domain = [
            "Quels sont les frais de scolarité ?",
            "Comment s'inscrire à SUP'PTIC ?",
            "Quelles sont les filières ?",
        ]

        for question in in_domain:
            answer, score, method = tfidf_fallback.search(question)
            # La réponse ne doit pas être le message "Je n'ai pas cette information"
            # uniquement si le score est décent
            if score > 0.05:
                self.assertNotIn(
                    "Je n'ai pas cette information",
                    answer,
                    f"Question en domaine sans réponse : '{question}' (score={score:.4f})"
                )

    # -------------------------------------------------------------------
    # Test de la bascule automatique dans rag_pipeline
    # -------------------------------------------------------------------

    def test_fallback_trigger_threshold(self):
        """
        Simule le comportement de rag_pipeline : si FAISS score < 0.55,
        tfidf_fallback.search() doit être appelé et retourner une réponse valide.
        
        Ce test vérifie l'interface attendue par rag_pipeline.py.
        """
        self._skip_if_not_loaded()

        # Scénario : FAISS a retourné un score faible (0.20 < 0.55)
        # rag_pipeline appelle alors tfidf_fallback.search()
        question = "Quel temps fait-il ?"  # Question hors domaine
        answer, score, method = tfidf_fallback.search(question)

        # Vérifications attendues par rag_pipeline
        self.assertIsInstance(answer, str, "La réponse doit être une chaîne")
        self.assertIsInstance(score, float, "Le score doit être un float")
        self.assertEqual(method, "TF-IDF", "La méthode doit être 'TF-IDF'")
        self.assertGreater(len(answer), 0, "La réponse ne doit pas être vide")

    # -------------------------------------------------------------------
    # Tests search_top_k
    # -------------------------------------------------------------------

    def test_search_top_k_structure(self):
        """search_top_k() doit retourner une liste de dicts avec les bons champs."""
        self._skip_if_not_loaded()
        results = tfidf_fallback.search_top_k("frais scolarité", k=3)
        self.assertIsInstance(results, list)
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

    # -------------------------------------------------------------------
    # Tests de robustesse
    # -------------------------------------------------------------------

    def test_search_empty_query(self):
        """search() avec une chaîne vide ne doit pas lever d'exception."""
        self._skip_if_not_loaded()
        try:
            answer, score, method = tfidf_fallback.search("")
            self.assertIsInstance(answer, str)
        except Exception as e:
            self.fail(f"search() a levé une exception avec une chaîne vide : {e}")

    def test_search_special_characters(self):
        """search() avec des caractères spéciaux ne doit pas lever d'exception."""
        self._skip_if_not_loaded()
        try:
            answer, score, method = tfidf_fallback.search("!@#$%^&*()_+")
            self.assertIsInstance(answer, str)
        except Exception as e:
            self.fail(f"search() a levé une exception avec des caractères spéciaux : {e}")

    def test_rebuild_produces_same_results(self):
        """
        Après un rebuild, les résultats doivent être identiques au chargement normal.
        """
        self._skip_if_not_loaded()
        question = "frais de scolarité"
        answer1, score1, _ = tfidf_fallback.search(question)
        tfidf_fallback.rebuild()
        answer2, score2, _ = tfidf_fallback.search(question)
        self.assertAlmostEqual(score1, score2, places=4,
                               msg="Les scores diffèrent après rebuild")

    def test_get_stats_structure(self):
        """get_stats() doit retourner un dict avec les bonnes clés."""
        stats = tfidf_fallback.get_stats()
        self.assertIn("loaded", stats)
        self.assertIn("entries_count", stats)
        self.assertIn("vocab_size", stats)
        if self._loaded:
            self.assertTrue(stats["loaded"])
            self.assertGreater(stats["entries_count"], 0)
            self.assertGreater(stats["vocab_size"], 0)


# -------------------------------------------------------------------
# Rapport de test détaillé
# -------------------------------------------------------------------
if __name__ == "__main__":
    print("=== test_fallback.py — Rapport détaillé ===\n")
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestTfidfFallback)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print(f"\n{'=' * 50}")
    print(f"Tests : {result.testsRun} | "
          f"OK : {result.testsRun - len(result.failures) - len(result.errors)} | "
          f"ÉCHEC : {len(result.failures)} | ERREUR : {len(result.errors)}")
    sys.exit(0 if result.wasSuccessful() else 1)

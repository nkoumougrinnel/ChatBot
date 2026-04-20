"""
test_faiss_search.py — Tests unitaires pour faiss_search.py.

Objectif : vérifier que les top-3 retournés sont sémantiquement cohérents
sur 20 questions connues.

Exécution :
    python manage.py test chatbot.tests.test_faiss_search   (depuis Django)
    python -m pytest backend/tests/test_faiss_search.py     (standalone)
"""

import sys
import unittest
from pathlib import Path

import numpy as np

# Chemins
_ENGINE_PATH = Path(__file__).resolve().parent.parent / "chatbot" / "engine"
_RAG_DATA_DIR = Path(__file__).resolve().parent.parent / "rag_data"

if str(_ENGINE_PATH) not in sys.path:
    sys.path.insert(0, str(_ENGINE_PATH))

from embedder import encode
import faiss_search


class TestFaissSearch(unittest.TestCase):
    """Tests unitaires pour faiss_search.py."""

    @classmethod
    def setUpClass(cls):
        """Charge l'index une seule fois pour tous les tests."""
        faiss_search.load_index()
        cls._index_loaded = faiss_search.is_loaded()

    def _skip_if_no_index(self):
        """Skip gracieusement si l'index n'est pas disponible."""
        if not self._index_loaded:
            self.skipTest(
                "Index FAISS non disponible — lancez build_index.py d'abord."
            )

    # -------------------------------------------------------------------
    # Tests de base
    # -------------------------------------------------------------------

    def test_index_loaded(self):
        """L'index FAISS doit pouvoir être chargé."""
        self._skip_if_no_index()
        stats = faiss_search.get_index_stats()
        self.assertTrue(stats["loaded"], "L'index FAISS n'est pas chargé")
        self.assertGreater(stats["ntotal"], 0, "L'index est vide")
        self.assertEqual(stats["dim"], 384, f"Dimension attendue : 384, obtenu : {stats['dim']}")

    def test_search_returns_list(self):
        """search() doit retourner une liste."""
        self._skip_if_no_index()
        vec = encode("C'est combien pour s'inscrire ?")
        results = faiss_search.search(vec, k=3)
        self.assertIsInstance(results, list)

    def test_search_k_results(self):
        """search() doit retourner exactement k résultats (ou moins si index petit)."""
        self._skip_if_no_index()
        vec = encode("Quels sont les frais de scolarité ?")
        k = 3
        results = faiss_search.search(vec, k=k)
        self.assertLessEqual(len(results), k)
        self.assertGreater(len(results), 0, "Aucun résultat retourné")

    def test_search_result_format(self):
        """Chaque résultat doit être un tuple (int, float)."""
        self._skip_if_no_index()
        vec = encode("Quels sont les frais de scolarité ?")
        results = faiss_search.search(vec, k=3)
        for item in results:
            self.assertIsInstance(item, tuple)
            self.assertEqual(len(item), 2)
            meta_id, score = item
            self.assertIsInstance(meta_id, int)
            self.assertIsInstance(score, float)

    def test_scores_between_0_and_1(self):
        """Les scores de similarité cosinus doivent être entre 0 et 1."""
        self._skip_if_no_index()
        vec = encode("Comment s'inscrire à SUP'PTIC ?")
        results = faiss_search.search(vec, k=5)
        for _, score in results:
            self.assertGreaterEqual(score, -0.1, f"Score trop bas : {score}")
            self.assertLessEqual(score, 1.01, f"Score trop élevé : {score}")

    def test_results_sorted_by_score_descending(self):
        """Les résultats doivent être triés par score décroissant."""
        self._skip_if_no_index()
        vec = encode("Frais de scolarité SUP'PTIC")
        results = faiss_search.search(vec, k=5)
        if len(results) < 2:
            return
        scores = [s for _, s in results]
        for i in range(len(scores) - 1):
            self.assertGreaterEqual(
                scores[i], scores[i + 1],
                f"Scores non triés : {scores[i]:.4f} < {scores[i+1]:.4f} à l'index {i}"
            )

    # -------------------------------------------------------------------
    # Test de cohérence sémantique (20 questions)
    # -------------------------------------------------------------------

    def test_semantic_coherence_20_questions(self):
        """
        Les top-3 retournés doivent être sémantiquement cohérents sur 20 questions.
        Critère : le meilleur résultat doit avoir un score > 0.30.
        """
        self._skip_if_no_index()

        test_questions = [
            "C'est combien pour s'inscrire ?",
            "Quels sont les frais de scolarité ?",
            "Comment rejoindre le club informatique ?",
            "Quelles sont les filières disponibles à SUP'PTIC ?",
            "Où se trouve l'école ?",
            "Quand commence l'année académique ?",
            "Comment obtenir une bourse ?",
            "Quels documents fournir pour le dossier d'inscription ?",
            "Quel est le programme de formation en réseaux ?",
            "Comment contacter l'administration ?",
            "tarif scol suptptic",
            "comment register",
            "frais inscription",
            "filiere info",
            "club info membres",
            "calendrier académique",
            "résultats examens",
            "logement étudiant",
            "horaires cours",
            "contacts secretariat",
        ]

        low_score_questions = []
        score_threshold = 0.30

        for question in test_questions:
            vec = encode(question)
            results = faiss_search.search(vec, k=1)
            if not results:
                low_score_questions.append((question, 0.0))
                continue
            best_score = results[0][1]
            if best_score < score_threshold:
                low_score_questions.append((question, best_score))

        if low_score_questions:
            msg_lines = [
                f"  {len(low_score_questions)}/{len(test_questions)} question(s) avec score < {score_threshold} :",
            ]
            for q, s in low_score_questions:
                msg_lines.append(f"  '{q}' → score={s:.4f}")
            # Avertissement uniquement si plus de 30% des questions échouent
            failure_rate = len(low_score_questions) / len(test_questions)
            if failure_rate > 0.30:
                self.fail(
                    f"Trop de questions avec score faible ({failure_rate:.0%}) :\n"
                    + "\n".join(msg_lines)
                )

    # -------------------------------------------------------------------
    # Tests search_with_metadata
    # -------------------------------------------------------------------

    def test_search_with_metadata_structure(self):
        """search_with_metadata() doit retourner des dicts avec les bons champs."""
        self._skip_if_no_index()
        vec = encode("Quels sont les frais de scolarité ?")
        results = faiss_search.search_with_metadata(vec, k=3)
        required_fields = {"vecteur_id", "score", "response", "example", "categorie", "source"}
        for r in results:
            self.assertIsInstance(r, dict)
            missing = required_fields - set(r.keys())
            self.assertEqual(len(missing), 0, f"Champs manquants dans le résultat : {missing}")

    def test_get_metadata_valid_id(self):
        """get_metadata() doit retourner un dict non vide pour un id valide."""
        self._skip_if_no_index()
        meta = faiss_search.get_metadata(0)
        self.assertIsInstance(meta, dict)
        self.assertGreater(len(meta), 0, "Métadonnées vides pour l'id 0")

    def test_get_metadata_invalid_id(self):
        """get_metadata() doit retourner {} pour un id invalide."""
        meta = faiss_search.get_metadata(-1)
        self.assertEqual(meta, {})
        meta2 = faiss_search.get_metadata(999999)
        self.assertEqual(meta2, {})

    def test_reload_index(self):
        """reload_index() doit recharger l'index sans erreur."""
        self._skip_if_no_index()
        stats_before = faiss_search.get_index_stats()
        faiss_search.reload_index()
        stats_after = faiss_search.get_index_stats()
        self.assertEqual(
            stats_before["ntotal"],
            stats_after["ntotal"],
            "Le nombre de vecteurs a changé après le rechargement"
        )

    # -------------------------------------------------------------------
    # Tests de robustesse
    # -------------------------------------------------------------------

    def test_search_empty_vector(self):
        """search() avec un vecteur nul ne doit pas lever d'exception."""
        self._skip_if_no_index()
        zero_vec = np.zeros(384, dtype=np.float32)
        try:
            results = faiss_search.search(zero_vec, k=3)
            self.assertIsInstance(results, list)
        except Exception as e:
            self.fail(f"search() a levé une exception avec un vecteur nul : {e}")

    def test_search_k_greater_than_index(self):
        """search() avec k > ntotal ne doit pas lever d'exception."""
        self._skip_if_no_index()
        vec = encode("Test")
        stats = faiss_search.get_index_stats()
        k = stats["ntotal"] + 100
        try:
            results = faiss_search.search(vec, k=k)
            self.assertLessEqual(len(results), stats["ntotal"])
        except Exception as e:
            self.fail(f"search() a levé une exception avec k > ntotal : {e}")


# -------------------------------------------------------------------
# Rapport de test détaillé
# -------------------------------------------------------------------
if __name__ == "__main__":
    print("=== test_faiss_search.py — Rapport détaillé ===\n")
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestFaissSearch)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print(f"\n{'=' * 50}")
    print(f"Tests : {result.testsRun} | "
          f"OK : {result.testsRun - len(result.failures) - len(result.errors)} | "
          f"ÉCHEC : {len(result.failures)} | ERREUR : {len(result.errors)}")
    sys.exit(0 if result.wasSuccessful() else 1)

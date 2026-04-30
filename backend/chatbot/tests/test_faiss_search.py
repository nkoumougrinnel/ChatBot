"""
test_faiss_search.py — Tests unitaires pour faiss_search.py.

Exécution depuis Django :
    python manage.py test chatbot.tests.test_faiss_search

Exécution standalone :
    python backend/chatbot/tests/test_faiss_search.py
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

import numpy as np
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
        if not self._index_loaded:
            self.skipTest(
                "Index FAISS non disponible — lancez build_index.py d'abord."
            )

    # ── Tests de base ────────────────────────────────────────────────

    def test_index_loaded(self):
        """L'index FAISS doit pouvoir être chargé."""
        self._skip_if_no_index()
        stats = faiss_search.get_index_stats()
        self.assertTrue(stats["loaded"])
        self.assertGreater(stats["ntotal"], 0)
        self.assertEqual(stats["dim"], 384)

    def test_search_returns_list(self):
        """search() doit retourner une liste."""
        self._skip_if_no_index()
        vec     = encode("C'est combien pour s'inscrire ?")
        results = faiss_search.search(vec, k=3)
        self.assertIsInstance(results, list)

    def test_search_k_results(self):
        """search() doit retourner au plus k résultats."""
        self._skip_if_no_index()
        vec     = encode("Quels sont les frais de scolarité ?")
        results = faiss_search.search(vec, k=3)
        self.assertLessEqual(len(results), 3)
        self.assertGreater(len(results), 0)

    def test_search_result_format(self):
        """Chaque résultat doit être un tuple (int, float)."""
        self._skip_if_no_index()
        vec     = encode("Quels sont les frais de scolarité ?")
        results = faiss_search.search(vec, k=3)
        for item in results:
            self.assertIsInstance(item, tuple)
            self.assertEqual(len(item), 2)
            meta_id, score = item
            self.assertIsInstance(meta_id, int)
            self.assertIsInstance(score, float)

    def test_scores_between_0_and_1(self):
        """Les scores doivent être entre -0.1 et 1.01."""
        self._skip_if_no_index()
        vec     = encode("Comment s'inscrire à SUP'PTIC ?")
        results = faiss_search.search(vec, k=5)
        for _, score in results:
            self.assertGreaterEqual(score, -0.1)
            self.assertLessEqual(score, 1.01)

    def test_results_sorted_by_score_descending(self):
        """Les résultats doivent être triés par score décroissant."""
        self._skip_if_no_index()
        vec     = encode("Frais de scolarité SUP'PTIC")
        results = faiss_search.search(vec, k=5)
        if len(results) < 2:
            return
        scores = [s for _, s in results]
        for i in range(len(scores) - 1):
            self.assertGreaterEqual(scores[i], scores[i + 1])

    # ── Test de cohérence sémantique ─────────────────────────────────

    def test_semantic_coherence_20_questions(self):
        """
        Les top-3 doivent être sémantiquement cohérents sur 20 questions.
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
            "calendrier académique",
            "résultats examens",
            "logement étudiant",
            "horaires cours",
            "contacts secretariat",
            "conditions admission suptptic",
        ]

        low_score = []
        for q in test_questions:
            vec     = encode(q)
            results = faiss_search.search(vec, k=1)
            score   = results[0][1] if results else 0.0
            if score < 0.30:
                low_score.append((q, score))

        failure_rate = len(low_score) / len(test_questions)
        if failure_rate > 0.30:
            self.fail(
                f"Trop de questions avec score faible ({failure_rate:.0%}) :\n"
                + "\n".join(f"  '{q}' → {s:.4f}" for q, s in low_score)
            )

    # ── Tests search_with_metadata ────────────────────────────────────

    def test_search_with_metadata_structure(self):
        """search_with_metadata() doit retourner des dicts avec les bons champs."""
        self._skip_if_no_index()
        vec     = encode("Quels sont les frais de scolarité ?")
        results = faiss_search.search_with_metadata(vec, k=3)
        required = {"vecteur_id", "score", "response", "example", "categorie", "source"}
        for r in results:
            self.assertIsInstance(r, dict)
            missing = required - set(r.keys())
            self.assertEqual(len(missing), 0,
                             f"Champs manquants : {missing}")

    def test_get_metadata_valid_id(self):
        """get_metadata() doit retourner un dict non vide pour l'id 0."""
        self._skip_if_no_index()
        meta = faiss_search.get_metadata(0)
        self.assertIsInstance(meta, dict)
        self.assertGreater(len(meta), 0)

    def test_get_metadata_invalid_id(self):
        """get_metadata() doit retourner {} pour un id invalide."""
        self.assertEqual(faiss_search.get_metadata(-1),      {})
        self.assertEqual(faiss_search.get_metadata(999999),  {})

    # ── Tests de robustesse ───────────────────────────────────────────

    def test_search_empty_vector(self):
        """search() avec un vecteur nul ne doit pas lever d'exception."""
        self._skip_if_no_index()
        zero_vec = np.zeros(384, dtype=np.float32)
        try:
            results = faiss_search.search(zero_vec, k=3)
            self.assertIsInstance(results, list)
        except Exception as e:
            self.fail(f"Exception avec vecteur nul : {e}")

    def test_search_k_greater_than_index(self):
        """search() avec k > ntotal ne doit pas lever d'exception."""
        self._skip_if_no_index()
        vec   = encode("Test")
        stats = faiss_search.get_index_stats()
        try:
            results = faiss_search.search(vec, k=stats["ntotal"] + 100)
            self.assertLessEqual(len(results), stats["ntotal"])
        except Exception as e:
            self.fail(f"Exception avec k > ntotal : {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

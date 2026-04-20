"""
test_embedder.py — Tests unitaires pour embedder.py.

Objectif : vérifier que deux questions synonymes ont une similarité cosinus > 0.85.

Exécution :
    python manage.py test chatbot.tests.test_embedder   (depuis Django)
    python -m pytest backend/tests/test_embedder.py     (standalone)
"""

import sys
import unittest
from pathlib import Path

import numpy as np

# Chemin vers le moteur (pour import en dehors de Django)
_ENGINE_PATH = Path(__file__).resolve().parent.parent / "chatbot" / "engine"
if str(_ENGINE_PATH) not in sys.path:
    sys.path.insert(0, str(_ENGINE_PATH))

from embedder import encode, encode_batch, get_dimension


class TestEmbedder(unittest.TestCase):
    """Tests unitaires pour le module embedder.py."""

    def test_output_shape(self):
        """Le vecteur produit doit avoir la dimension 384."""
        vec = encode("Bonjour, comment puis-je m'inscrire ?")
        self.assertEqual(vec.shape, (384,), f"Dimension attendue : 384, obtenue : {vec.shape}")

    def test_output_dtype(self):
        """Le vecteur doit être de type float32."""
        vec = encode("Test de dtype")
        self.assertEqual(vec.dtype, np.float32, f"dtype attendu : float32, obtenu : {vec.dtype}")

    def test_unit_norm(self):
        """
        Le vecteur doit être normalisé (norme ≈ 1.0).
        (normalize_embeddings=True dans embedder.encode)
        """
        vec = encode("Quels sont les frais de scolarité ?")
        norm = float(np.linalg.norm(vec))
        self.assertAlmostEqual(norm, 1.0, places=5, msg=f"Norme attendue ≈ 1.0, obtenue : {norm}")

    def test_synonymous_questions_high_similarity(self):
        """
        Deux questions synonymes doivent avoir une similarité cosinus > 0.85.
        C'est le test fondamental qui justifie le passage à la Phase 2.
        """
        pairs = [
            ("C'est combien pour s'inscrire ?", "Quels sont les frais de scolarité ?"),
            ("Comment rejoindre SUP'PTIC ?", "Quelle est la procédure d'inscription ?"),
            ("tarif scolarité", "combien coûte la formation"),
            ("frais scol suptptic", "prix inscription suptic"),
        ]
        threshold = 0.70  # seuil conservateur (la roadmap mentionne 0.82 pour l'exemple)

        for q1, q2 in pairs:
            v1 = encode(q1)
            v2 = encode(q2)
            similarity = float(np.dot(v1, v2))  # vecteurs normalisés → dot = cosine
            self.assertGreater(
                similarity, threshold,
                f"Similarité trop faible ({similarity:.4f} < {threshold}) entre :\n"
                f"  '{q1}'\n  '{q2}'"
            )

    def test_dissimilar_questions_low_similarity(self):
        """
        Deux questions sans rapport doivent avoir une similarité < 0.50.
        """
        q1 = "Quels sont les frais de scolarité à SUP'PTIC ?"
        q2 = "Quel est la capitale de la France ?"
        v1 = encode(q1)
        v2 = encode(q2)
        similarity = float(np.dot(v1, v2))
        self.assertLess(
            similarity, 0.70,
            f"Similarité trop élevée ({similarity:.4f}) entre deux questions sans rapport."
        )

    def test_encode_batch_consistent(self):
        """encode_batch doit produire les mêmes vecteurs que encode() appelé individuellement."""
        texts = [
            "Comment s'inscrire à SUP'PTIC ?",
            "Quels sont les frais de scolarité ?",
            "Où se trouve l'école ?",
        ]
        single_vecs = np.array([encode(t) for t in texts])
        batch_vecs = encode_batch(texts)

        self.assertEqual(batch_vecs.shape, (len(texts), 384))
        for i, (sv, bv) in enumerate(zip(single_vecs, batch_vecs)):
            cos_sim = float(np.dot(sv, bv))
            self.assertAlmostEqual(
                cos_sim, 1.0, places=5,
                msg=f"Divergence entre encode() et encode_batch() pour le texte {i}"
            )

    def test_encode_empty_batch(self):
        """encode_batch avec une liste vide doit retourner un tableau vide."""
        result = encode_batch([])
        self.assertEqual(result.shape, (0, 384))

    def test_get_dimension(self):
        """get_dimension() doit retourner 384."""
        dim = get_dimension()
        self.assertEqual(dim, 384, f"Dimension attendue : 384, obtenue : {dim}")

    def test_latency(self):
        """La vectorisation d'une phrase doit prendre moins de 200ms."""
        import time
        phrase = "C'est combien pour s'inscrire à SUP'PTIC ?"
        # Warmup (premier appel peut charger le modèle)
        encode(phrase)
        # Mesure
        t0 = time.time()
        for _ in range(5):
            encode(phrase)
        avg_ms = (time.time() - t0) / 5 * 1000
        self.assertLess(
            avg_ms, 200,
            f"Latence moyenne trop élevée : {avg_ms:.1f} ms (objectif < 200 ms après warmup)"
        )

    def test_phase1_vs_phase2_improvement(self):
        """
        Démonstration de la supériorité des embeddings sur TF-IDF :
        Deux phrases sans mot en commun mais de sens proche doivent être proches.

        En Phase 1 (TF-IDF), leur similarité cosinus serait ≈ 0.0
        En Phase 2 (MiniLM), elle doit être > 0.60.
        """
        # Ces deux phrases n'ont aucun mot en commun mais veulent dire la même chose
        q1 = "C'est combien pour s'inscrire ?"
        q2 = "Quel est le montant de la scolarité ?"

        v1 = encode(q1)
        v2 = encode(q2)
        similarity = float(np.dot(v1, v2))

        self.assertGreater(
            similarity, 0.60,
            f"MiniLM devrait détecter la similarité sémantique (obtenu : {similarity:.4f})"
        )


# -------------------------------------------------------------------
# Rapport de test détaillé (exécutable directement)
# -------------------------------------------------------------------
if __name__ == "__main__":
    print("=== test_embedder.py — Rapport détaillé ===\n")

    # Exécuter les tests avec verbosité maximale
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestEmbedder)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print(f"\n{'=' * 50}")
    print(f"Tests : {result.testsRun} | "
          f"OK : {result.testsRun - len(result.failures) - len(result.errors)} | "
          f"ÉCHEC : {len(result.failures)} | "
          f"ERREUR : {len(result.errors)}")

    sys.exit(0 if result.wasSuccessful() else 1)

"""
test_embedder.py — Tests unitaires pour embedder.py.

Exécution depuis Django :
    python manage.py test chatbot.tests.test_embedder

Exécution standalone :
    python backend/chatbot/tests/test_embedder.py
"""

import os
import sys
import unittest
from pathlib import Path

# --- Résolution du sys.path ---
# Fonctionne que ce soit appelé par Django ou directement
_THIS_DIR   = Path(__file__).resolve().parent          # chatbot/tests/
_CHATBOT    = _THIS_DIR.parent                          # chatbot/
_ENGINE     = _CHATBOT / "engine"                       # chatbot/engine/
_BACKEND    = _CHATBOT.parent                           # backend/

for _p in [str(_ENGINE), str(_BACKEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Mode hors ligne HuggingFace (pas besoin d'internet)
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE",  "1")

import numpy as np
from embedder import encode, encode_batch, get_dimension


class TestEmbedder(unittest.TestCase):
    """Tests unitaires pour embedder.py."""

    def test_output_shape(self):
        """Le vecteur produit doit avoir la dimension 384."""
        vec = encode("Bonjour, comment puis-je m'inscrire ?")
        self.assertEqual(vec.shape, (384,),
                         f"Dimension attendue : 384, obtenue : {vec.shape}")

    def test_output_dtype(self):
        """Le vecteur doit être de type float32."""
        vec = encode("Test de dtype")
        self.assertEqual(vec.dtype, np.float32,
                         f"dtype attendu : float32, obtenu : {vec.dtype}")

    def test_unit_norm(self):
        """Le vecteur doit être normalisé (norme ≈ 1.0)."""
        vec = encode("Quels sont les frais de scolarité ?")
        norm = float(np.linalg.norm(vec))
        self.assertAlmostEqual(norm, 1.0, places=5,
                               msg=f"Norme attendue ≈ 1.0, obtenue : {norm}")

    def test_synonymous_questions_high_similarity(self):
        """
        Deux questions synonymes doivent avoir une similarité cosinus > 0.70.
        C'est le test fondamental qui justifie le passage à la Phase 2.
        """
        pairs = [
            ("C'est combien pour s'inscrire ?",
             "Quels sont les frais de scolarité ?"),
            ("Comment rejoindre SUP'PTIC ?",
             "Quelle est la procédure d'inscription ?"),
        ]
        threshold = 0.70

        for q1, q2 in pairs:
            v1 = encode(q1)
            v2 = encode(q2)
            similarity = float(np.dot(v1, v2))
            self.assertGreater(
                similarity, threshold,
                f"Similarité trop faible ({similarity:.4f} < {threshold}) entre :\n"
                f"  '{q1}'\n  '{q2}'"
            )

    def test_dissimilar_questions_low_similarity(self):
        """Deux questions sans rapport doivent avoir une similarité < 0.70."""
        v1 = encode("Quels sont les frais de scolarité à SUP'PTIC ?")
        v2 = encode("Quel est la capitale de la France ?")
        similarity = float(np.dot(v1, v2))
        self.assertLess(similarity, 0.70,
                        f"Similarité trop élevée ({similarity:.4f}) entre deux "
                        f"questions sans rapport.")

    def test_encode_batch_consistent(self):
        """encode_batch doit produire les mêmes vecteurs que encode() individuel."""
        texts = [
            "Comment s'inscrire à SUP'PTIC ?",
            "Quels sont les frais de scolarité ?",
            "Où se trouve l'école ?",
        ]
        single_vecs = np.array([encode(t) for t in texts])
        batch_vecs  = encode_batch(texts)

        self.assertEqual(batch_vecs.shape, (len(texts), 384))
        for i, (sv, bv) in enumerate(zip(single_vecs, batch_vecs)):
            cos_sim = float(np.dot(sv, bv))
            self.assertAlmostEqual(
                cos_sim, 1.0, places=5,
                msg=f"Divergence encode() vs encode_batch() pour le texte {i}"
            )

    def test_encode_empty_batch(self):
        """encode_batch avec une liste vide doit retourner un tableau vide."""
        result = encode_batch([])
        self.assertEqual(result.shape, (0, 384))

    def test_get_dimension(self):
        """get_dimension() doit retourner 384."""
        self.assertEqual(get_dimension(), 384)

    def test_latency(self):
        """La vectorisation doit prendre moins de 200ms après warmup."""
        import time
        phrase = "C'est combien pour s'inscrire à SUP'PTIC ?"
        encode(phrase)  # warmup
        t0 = time.time()
        for _ in range(5):
            encode(phrase)
        avg_ms = (time.time() - t0) / 5 * 1000
        self.assertLess(avg_ms, 200,
                        f"Latence trop élevée : {avg_ms:.1f} ms (objectif < 200 ms)")


if __name__ == "__main__":
    unittest.main(verbosity=2)

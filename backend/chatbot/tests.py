"""Tests de l'application chatbot : fonctions pures et logique de recherche."""

from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from chatbot import similarity, utils


class CosineSimilarityTests(SimpleTestCase):
    """La similarité cosinus ne dépend ni de la base ni du ML lourd."""

    def test_identical_vectors_return_one(self):
        score = similarity.compute_cosine_similarity([1, 0, 1], [1, 0, 1])
        self.assertAlmostEqual(score, 1.0, places=5)

    def test_orthogonal_vectors_return_zero(self):
        score = similarity.compute_cosine_similarity([1, 0], [0, 1])
        self.assertAlmostEqual(score, 0.0, places=5)

    def test_zero_vector_returns_zero(self):
        self.assertEqual(similarity.compute_cosine_similarity([0, 0], [1, 1]), 0.0)

    def test_score_is_clamped_between_zero_and_one(self):
        score = similarity.compute_cosine_similarity([2, 2], [1, 1])
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


class ConversationalRuleTests(SimpleTestCase):
    """Le niveau 0 (règles conversationnelles) fonctionne sans vectorisation."""

    def test_matching_pattern_returns_response(self):
        rules = [{"intent": "salutation", "patterns": ["bonjour"], "response": "Bonjour !"}]
        with patch.object(similarity, "CONVERSATIONAL_RULES", rules):
            self.assertEqual(
                similarity.match_conversational_rule("Bonjour, ça va ?"), "Bonjour !"
            )

    def test_no_match_returns_none(self):
        rules = [{"intent": "salutation", "patterns": ["bonjour"], "response": "Bonjour !"}]
        with patch.object(similarity, "CONVERSATIONAL_RULES", rules):
            self.assertIsNone(similarity.match_conversational_rule("Quels sont les frais ?"))


class GetChatbotResponseTests(TestCase):
    """Vérifie le formatage et les seuils de confiance de get_chatbot_response."""

    class _FakeFAQ:
        id = 1
        question = "Q"
        answer = "A"

    @patch("chatbot.utils.find_best_faq")
    def test_confident_status_for_high_score(self, mock_find):
        mock_find.return_value = [{"faq": self._FakeFAQ(), "score": 0.9}]
        result = utils.get_chatbot_response("Q", top_k=1)
        self.assertEqual(result["status"], "confident")
        self.assertEqual(result["count"], 1)
        mock_find.assert_called_once_with("Q", top_k=1)

    @patch("chatbot.utils.find_best_faq")
    def test_uncertain_status_for_medium_score(self, mock_find):
        mock_find.return_value = [{"faq": self._FakeFAQ(), "score": 0.7}]
        result = utils.get_chatbot_response("Q")
        self.assertEqual(result["status"], "uncertain")

    @patch("chatbot.utils.find_best_faq")
    def test_not_found_status_for_empty_results(self, mock_find):
        mock_find.return_value = []
        result = utils.get_chatbot_response("Q")
        self.assertEqual(result["status"], "not found")
        self.assertEqual(result["count"], 0)

"""Tests de l'application FAQ : modèles, signaux et endpoints API."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from faq.models import Category, FAQ, FAQVector, Feedback

User = get_user_model()


class ModelTests(TestCase):
    """Vérifie le comportement de base des modèles."""

    def setUp(self):
        self.category = Category.objects.create(name="Support")
        self.faq = FAQ.objects.create(
            question="Comment réinitialiser mon mot de passe ?",
            answer="Cliquez sur « mot de passe oublié ».",
            category=self.category,
        )

    def test_category_str(self):
        self.assertEqual(str(self.category), "Support")

    def test_faq_defaults(self):
        self.assertTrue(self.faq.is_active)
        self.assertEqual(self.faq.popularity, 0)

    def test_faq_str_is_truncated(self):
        self.assertEqual(str(self.faq), self.faq.question[:100])

    def test_feedback_str(self):
        user = User.objects.create_user(username="alice", password="secret123")
        feedback = Feedback.objects.create(
            user=user,
            faq=self.faq,
            feedback_type="positif",
            question_utilisateur="mot de passe",
        )
        self.assertIn("positif", str(feedback))


class FeedbackSignalTests(TestCase):
    """Vérifie que le signal post_save ajuste popularité et norme du vecteur."""

    def setUp(self):
        self.user = User.objects.create_user(username="bob", password="secret123")
        self.category = Category.objects.create(name="Support")
        self.faq = FAQ.objects.create(question="Q", answer="A", category=self.category)
        self.vector = FAQVector.objects.create(
            faq=self.faq, tfidf_vector=[0.1, 0.2], norm=0.5
        )

    def test_positive_feedback_increments_popularity_and_norm(self):
        Feedback.objects.create(
            user=self.user,
            faq=self.faq,
            feedback_type="positif",
            question_utilisateur="Q",
            score_similarite=0.9,
        )
        self.faq.refresh_from_db()
        self.vector.refresh_from_db()
        self.assertEqual(self.faq.popularity, 1)
        self.assertAlmostEqual(self.vector.norm, min(0.5 * 1.1, 1.0), places=5)

    def test_negative_feedback_reduces_norm_without_popularity(self):
        Feedback.objects.create(
            user=self.user,
            faq=self.faq,
            feedback_type="negatif",
            question_utilisateur="Q",
            score_similarite=0.8,
        )
        self.faq.refresh_from_db()
        self.vector.refresh_from_db()
        self.assertEqual(self.faq.popularity, 0)
        self.assertAlmostEqual(self.vector.norm, max(0.5 * 0.9, 0.1), places=5)


class ApiTests(APITestCase):
    """Vérifie les endpoints publics et les protections d'accès."""

    def setUp(self):
        self.category = Category.objects.create(name="Support")
        self.faq = FAQ.objects.create(question="Q1", answer="A1", category=self.category)

    def test_list_categories_is_public(self):
        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_faq_is_public(self):
        response = self.client.get("/api/faq/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_category_requires_authentication(self):
        response = self.client.post("/api/categories/", {"name": "Nouvelle"})
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    @patch("faq.views.find_best_faq")
    def test_chatbot_ask_returns_confident_result(self, mock_find_best_faq):
        mock_find_best_faq.return_value = [{"faq": self.faq, "score": 0.95}]
        response = self.client.post(
            "/api/chatbot/ask/",
            {"question": "Q1", "top_k": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["status"], "confident")

    @patch("faq.views.find_best_faq")
    def test_chatbot_ask_validates_empty_question(self, mock_find_best_faq):
        response = self.client.post("/api/chatbot/ask/", {"top_k": 1}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_find_best_faq.assert_not_called()

    def test_anonymous_feedback_creation(self):
        response = self.client.post(
            "/api/feedback/",
            {
                "faq": self.faq.id,
                "feedback_type": "positif",
                "question_utilisateur": "Q1",
            },
            format="json",
        )
        self.assertIn(
            response.status_code,
            (status.HTTP_200_OK, status.HTTP_201_CREATED),
        )
        self.assertEqual(Feedback.objects.count(), 1)

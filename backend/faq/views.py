"""
faq/views.py — Vues API REST Phase 1 (inchangées).

Endpoints :
    GET/POST  /api/categories/           CategoryViewSet
    GET/POST  /api/faq/                  FAQViewSet
    GET/POST  /api/feedback/             FeedbackViewSet
    GET       /api/stats/                faq_stats
    GET       /api/stats/categories/     category_stats

Note : le ChatbotAskViewSet (TF-IDF Phase 1) est supprimé.
       Le pipeline RAG Gen3 est dans chatbot/views.py.
"""

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q
from django.core.cache import cache

from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from faq.models import Category, FAQ, Feedback
from faq.serializers import (
    CategorySerializer,
    FAQSerializer,
    FAQListSerializer,
    FeedbackSerializer,
)


# ─────────────────────────────────────────────────────────────────────────────
# Catégories
# ─────────────────────────────────────────────────────────────────────────────

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [IsAuthenticated()]
        return [AllowAny()]


# ─────────────────────────────────────────────────────────────────────────────
# FAQs
# ─────────────────────────────────────────────────────────────────────────────

class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.filter(is_active=True).select_related('category')

    def get_serializer_class(self):
        if self.action == 'list':
            return FAQListSerializer
        return FAQSerializer

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [IsAuthenticated()]
        return [AllowAny()]


# ─────────────────────────────────────────────────────────────────────────────
# Feedback
# ─────────────────────────────────────────────────────────────────────────────

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all().select_related('user', 'faq')
    serializer_class = FeedbackSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Assigne l'utilisateur courant ou l'utilisateur anonyme."""
        User = get_user_model()

        if self.request.user and self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            anon_user, _ = User.objects.get_or_create(
                username='anonymous',
                defaults={
                    'email':    'anonymous@chatbot.local',
                    'password': 'anonymous',
                }
            )
            serializer.save(user=anon_user)


# ─────────────────────────────────────────────────────────────────────────────
# Statistiques
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
def faq_stats(request):
    """GET /api/stats/ — FAQs triées par taux de satisfaction."""
    stats = FAQ.objects.annotate(
        avg_satisfaction=Avg('feedback__score_similarite'),
        positive_feedbacks=Count(
            'feedback', filter=Q(feedback__feedback_type='positif')
        )
    ).order_by('-avg_satisfaction')

    data = [
        {
            "id":    item.id,
            "question": item.question,
            "avg_score": round(item.avg_satisfaction or 0, 4),
            "count": item.positive_feedbacks,
        }
        for item in stats
    ]
    return Response(data)


@api_view(['GET'])
def category_stats(request):
    """GET /api/stats/categories/ — Répartition par catégorie."""
    categories = Category.objects.annotate(faq_count=Count('faq'))
    data = [
        {"name": cat.name, "count": cat.faq_count}
        for cat in categories
    ]
    return Response(data)

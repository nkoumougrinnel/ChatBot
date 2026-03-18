"""
Vues API REST pour le chatbot.

Endpoints :
- GET/POST /api/faq/         : lister et créer FAQs
- GET      /api/faq/{id}/    : détail FAQ
- GET      /api/categories/  : lister catégories
- POST     /api/categories/  : créer catégorie
- POST     /api/chatbot/ask/ : poser une question et obtenir réponses pertinentes
- POST     /api/feedback/    : envoyer un feedback
- GET      /api/stats/       : statistiques FAQ
- GET      /api/stats/categories/ : statistiques par catégorie
"""

from rest_framework import viewsets, status
from django.db.models import Count, Avg
from django.core.cache import cache
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from faq.models import Category, FAQ, Feedback
from faq.serializers import (
    CategorySerializer,
    FAQSerializer,
    FAQListSerializer,
    FeedbackSerializer,
    QuestionRequestSerializer,
    ChatbotResponseSerializer,
)
from chatbot.utils import find_best_faq


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
# Chatbot — endpoint principal
# ─────────────────────────────────────────────────────────────────────────────

class ChatbotAskViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'], url_path='ask')
    def ask(self, request):
        serializer = QuestionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        question = serializer.validated_data['question']
        top_k = serializer.validated_data.get('top_k', 3)

        # 1. Cache
        cache_key = f"query_{question.strip().lower()}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached, status=status.HTTP_200_OK)

        # 2. Recherche TF-IDF
        try:
            faq_results = find_best_faq(question, top_k=top_k)
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la recherche : {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 3. Formatage + seuils de confiance
        results = []
        status_confidence = "not found"

        for faq_result in faq_results:
            faq = faq_result['faq']
            score = faq_result['score']

            if score >= 0.8:
                status_confidence = "confident"
            elif score >= 0.6 and status_confidence != "confident":
                status_confidence = "uncertain"

            results.append({
                'faq_id': faq.id,
                'question': faq.question,
                'answer': faq.answer,
                'score': round(score, 4),
                'category': faq.category.name,
            })

        response_data = {
            'question': question,
            'results': results,
            'count': len(results),
            'status': status_confidence,
        }

        cache.set(cache_key, response_data, 3600)

        response_serializer = ChatbotResponseSerializer(response_data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


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
        from django.contrib.auth import get_user_model
        User = get_user_model()

        if self.request.user and self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            anon_user, _ = User.objects.get_or_create(
                username='anonymous',
                defaults={'email': 'anonymous@chatbot.local', 'is_active': True}
            )
            serializer.save(user=anon_user)


# ─────────────────────────────────────────────────────────────────────────────
# Statistiques (vues standalone)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
def faq_stats(request):
    """GET /api/stats/ — FAQs triées par taux de satisfaction moyen."""
    stats = FAQ.objects.annotate(
        avg_satisfaction=Avg('feedback__score_similarite'),
        total_feedbacks=Count('feedback'),
    ).order_by('-avg_satisfaction')

    data = [
        {
            'id': item.id,
            'question': item.question,
            'avg_score': round(item.avg_satisfaction or 0, 4),
            'count': item.total_feedbacks,
        }
        for item in stats
    ]
    return Response(data)


@api_view(['GET'])
def category_stats(request):
    """GET /api/stats/categories/ — Répartition des FAQs par catégorie."""
    categories = Category.objects.annotate(faq_count=Count('faq'))
    data = [{'name': cat.name, 'count': cat.faq_count} for cat in categories]
    return Response(data)

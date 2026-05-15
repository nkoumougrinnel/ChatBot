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
from django.db.models import Count, Avg, Q
from django.core.cache import cache
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count, Avg
from django.core.cache import cache

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
from chatbot.engine.tfidf_fallback import search as tfidf_search, is_loaded as tfidf_loaded


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

        # 2. Recherche principale
        try:
            faq_results = find_best_faq(question, top_k=top_k)
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la recherche : {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 3. Fallback TF-IDF historique si aucune FAQ active / aucun résultat
        if not faq_results and tfidf_loaded():
            tfidf_answer, tfidf_score, _ = tfidf_search(question)
            if tfidf_answer:
                results = [{
                    'faq_id': 0,
                    'question': question,
                    'answer': tfidf_answer,
                    'score': round(tfidf_score, 4),
                    'category': 'fallback',
                }]
                status_confidence = 'confident' if tfidf_score >= 0.8 else 'uncertain' if tfidf_score >= 0.6 else 'not found'
                response_data = {
                    'question': question,
                    'results': results,
                    'count': len(results),
                    'status': status_confidence,
                }
                cache.set(cache_key, response_data, 3600)
                response_serializer = ChatbotResponseSerializer(response_data)
                return Response(response_serializer.data, status=status.HTTP_200_OK)

        # 4. Formatage du résultat principal
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

@api_view(['GET'])
def faq_stats(request):
    """GET /api/stats/ - FAQ par taux de satisfaction (count = feedbacks positifs)"""
    # Calcul de la moyenne des scores et compte des feedbacks POSITIFS
    stats = FAQ.objects.annotate(
        avg_satisfaction=Avg('feedback__score_similarite'),
        positive_feedbacks=Count('feedback', filter=Q(feedback__feedback_type='positif'))
    ).order_by('-avg_satisfaction')
    data = []
    for item in stats:
        data.append({
            "id": item.id,
            "question": item.question,
            "avg_score": round((item.avg_satisfaction or 0), 4),
            "count": item.positive_feedbacks
        })
    return Response(data)


@api_view(['GET'])
def category_stats(request):
    """GET /api/stats/categories/ - Répartition par catégorie"""
    categories = Category.objects.annotate(faq_count=Count('faq'))
    data = [{"name": cat.name, "count": cat.faq_count} for cat in categories]
    return Response(data)


class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all().select_related('user', 'faq')
    serializer_class = FeedbackSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Assigner l'utilisateur courant ou anonyme selon l'authentification."""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        if self.request.user and self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            # Utilisateur anonyme : créer/récupérer un user anonyme
            try:
                anon_user = User.objects.get(username='anonymous')
            except User.DoesNotExist:
                anon_user = User.objects.create_user(
                    username='anonymous',
                    email='anonymous@chatbot.local',
                    password='anonymous'
                )
            serializer.save(user=anon_user)
            
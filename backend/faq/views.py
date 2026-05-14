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
        """
        Poser une question et retourner les FAQs les plus pertinentes.
        
        Body:
        {
            "question": "Comment réinitialiser mon mot de passe ?",
            "top_k": 3
        }
        
        Response:
        {
            "question": "Comment réinitialiser mon mot de passe ?",
            "results": [
                {
                    "faq_id": 1,
                    "question": "...",
                    "answer": "...",
                    "score": 0.95,
                    "category": "Support"
                }
            ],
            "count": 1
        }
        """
        serializer = QuestionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        question = serializer.validated_data['question']
        top_k = serializer.validated_data.get('top_k', 1)
        
        # ===== 1. Vérifier le cache =====
        import hashlib
        cache_key = f"query_{hashlib.md5(question.strip().lower().encode()).hexdigest()}"
        cached_response = cache.get(cache_key)
        if cached_response:
            return Response(cached_response, status=status.HTTP_200_OK)
        
        # ===== 2. Recherche TF-IDF =====
        try:
            faq_results = find_best_faq(question, top_k=top_k)
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la recherche : {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Formater les résultats
        results = []
        status_confidence = "not found"
        
        for faq_result in faq_results:
            faq = faq_result['faq']
            score = faq_result['score']
            
            # Déterminer le statut de confiance
            if score < 0.6:
                if status_confidence == "not found":
                    status_confidence = "not found"
            elif 0.6 <= score < 0.8:
                if status_confidence != "confident":
                    status_confidence = "uncertain"
            else:
                status_confidence = "confident"
            
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
            
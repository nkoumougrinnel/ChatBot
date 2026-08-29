"""
Serializers pour l'API REST du chatbot.

Définit les schémas de sérialisation/désérialisation pour :
- Category : catégories de FAQs
- FAQ : paires question-réponse
- FAQVector : vecteurs TF-IDF (lecture seule)
- Feedback : retours utilisateurs
- QuestionRequest : requête de l'utilisateur (POST /api/chatbot/ask/)
"""

from rest_framework import serializers
from faq.models import Category, FAQ, FAQVector, Feedback


class CategorySerializer(serializers.ModelSerializer):
    """Sérialisation des catégories FAQs."""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'active']
        read_only_fields = ['id']


class FAQVectorSerializer(serializers.ModelSerializer):
    """Sérialisation des vecteurs TF-IDF (lecture seule)."""
    
    class Meta:
        model = FAQVector
        fields = ['id', 'norm', 'computed_at']
        read_only_fields = ['id', 'norm', 'computed_at']


class FAQSerializer(serializers.ModelSerializer):
    """Sérialisation complète des FAQs avec catégorie."""
    
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True,
        source='category'
    )
    vector = FAQVectorSerializer(read_only=True)
    
    class Meta:
        model = FAQ
        fields = [
            'id',
            'question',
            'answer',
            'category',
            'category_id',
            'subtheme',
            'source',
            'created_at',
            'updated_at',
            'is_active',
            'popularity',
            'vector',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FAQListSerializer(serializers.ModelSerializer):
    """Sérialisation légère des FAQs (pour listage)."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = FAQ
        fields = [
            'id',
            'question',
            'category_name',
            'subtheme',
            'is_active',
            'popularity',
        ]
        read_only_fields = fields


def _resolve_faq_fast(question: str) -> FAQ | None:
    """Résolution rapide via TF-IDF (évite le scan complet Phase 1)."""
    from chatbot.engine.tfidf_fallback import search_top_k

    hits = search_top_k(question, k=1)
    if not hits or float(hits[0].get("score", 0)) < 0.32:
        return None
    ref_q = (hits[0].get("question") or "").strip()
    if not ref_q:
        return None
    faq = FAQ.objects.filter(is_active=True, question__iexact=ref_q).first()
    if faq:
        return faq
    return FAQ.objects.filter(is_active=True, question__icontains=ref_q[:80]).first()


class FeedbackSerializer(serializers.ModelSerializer):
    """Sérialisation des feedbacks utilisateurs."""

    user_username = serializers.CharField(source='user.username', read_only=True)
    faq_question = serializers.CharField(source='faq.question', read_only=True)
    faq = serializers.PrimaryKeyRelatedField(
        queryset=FAQ.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Feedback
        fields = [
            'id',
            'user',
            'user_username',
            'faq',
            'faq_question',
            'feedback_type',
            'question_utilisateur',
            'comment',
            'score_similarite',
            'created_at',
        ]
        read_only_fields = ['id', 'user', 'user_username', 'created_at']

    def validate(self, attrs):
        faq = attrs.get('faq')
        question = (attrs.get('question_utilisateur') or '').strip()

        if not faq:
            if not question:
                raise serializers.ValidationError({
                    'question_utilisateur': "Requis lorsque l'identifiant FAQ n'est pas fourni.",
                })
            faq = _resolve_faq_fast(question)
            if not faq:
                raise serializers.ValidationError(
                    'Aucune FAQ correspondante pour enregistrer ce feedback.'
                )
            attrs['faq'] = faq
            if attrs.get('score_similarite') is None:
                attrs['score_similarite'] = 0.0
        elif not question:
            attrs['question_utilisateur'] = faq.question

        return attrs


class QuestionRequestSerializer(serializers.Serializer):
    """Sérialisation d'une requête de question (POST /api/chatbot/ask/)."""
    
    question = serializers.CharField(
        max_length=1000,
        help_text="Question posée par l'utilisateur"
    )
    top_k = serializers.IntegerField(
        default=3,
        min_value=1,
        max_value=10,
        help_text="Nombre de résultats à retourner (défaut: 3)"
    )


class ChatbotResponseSerializer(serializers.Serializer):
    """Sérialisation d'une réponse du chatbot avec statut de confiance."""

    question = serializers.CharField()
    results = serializers.ListField(
        child=serializers.DictField()
    )
    count = serializers.IntegerField()
    status = serializers.CharField(
        help_text="Status de confiance: 'not found', 'uncertain', ou 'confident'"
    )
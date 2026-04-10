from django.db import models
from django.conf import settings


class Category(models.Model):
    """
    Catégories pour classifier les questions FAQ.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom")
    description = models.TextField(blank=True, verbose_name="Description")
    active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

    def __str__(self):
        return self.name


class FAQ(models.Model):
    """
    Paires question-réponse - cœur du système.
    """
    question = models.TextField(verbose_name="Question")
    answer = models.TextField(verbose_name="Réponse")
    category = models.ForeignKey(Category, on_delete=models.RESTRICT, verbose_name="Catégorie")
    subtheme = models.CharField(max_length=100, blank=True, verbose_name="Sous-thème")
    source = models.CharField(max_length=200, blank=True, verbose_name="Source")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date modification")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    popularity = models.IntegerField(default=0, verbose_name="Popularité")

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
        ordering = ['category', 'subtheme', 'question']

    def __str__(self):
        return self.question[:100]


class FAQVector(models.Model):
    """
    Vecteurs TF-IDF pré-calculés pour chaque FAQ.
    Utilisé pour la recherche par similarité.
    """
    faq = models.OneToOneField(FAQ, on_delete=models.CASCADE, related_name='vector', verbose_name="FAQ associée")
    tfidf_vector = models.JSONField(verbose_name="Vecteur TF-IDF")
    norm = models.FloatField(verbose_name="Norme du vecteur")
    computed_at = models.DateTimeField(auto_now_add=True, verbose_name="Calculé le")

    class Meta:
        verbose_name = "Vecteur FAQ"
        verbose_name_plural = "Vecteurs FAQ"

    def __str__(self):
        return f"Vecteur FAQ #{self.faq.id}"


class Feedback(models.Model):
    """
    Retours utilisateurs sur la pertinence des réponses.
    """
    FEEDBACK_TYPES = [
        ('positif', 'Positif'),
        ('negatif', 'Négatif'),
    ]
    METHOD_CHOICES = [
        ('TF-IDF', 'TF-IDF'),
        ('RAG', 'RAG'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Utilisateur")
    faq = models.ForeignKey(FAQ, on_delete=models.CASCADE, verbose_name="FAQ concernée")
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES, verbose_name="Type")
    question_utilisateur = models.TextField(verbose_name="Question utilisateur")
    comment = models.TextField(blank=True, verbose_name="Commentaire")
    rag_method = models.CharField(max_length=10, choices=METHOD_CHOICES, default='TF-IDF')
    score_similarite = models.FloatField(null=True, blank=True, verbose_name="Score de similarité")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date création")

    class Meta:
        verbose_name = "Feedback"
        verbose_name_plural = "Feedbacks"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.feedback_type} sur FAQ #{self.faq.id}"

from django.db import models


class Feedback(models.Model):
    """Feedback léger associé à une réponse Gen3 (méthode RAG utilisée)."""

    message_id = models.CharField(max_length=100, blank=True)
    fb_type = models.CharField(max_length=10)  # "like" ou "dislike"
    rag_method = models.CharField(max_length=10, default="TF-IDF")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fb_type} - {self.rag_method} - {self.message_id}"

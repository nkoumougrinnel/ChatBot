from django.apps import AppConfig

class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'
    def ready(self):
      """" Charge de l'index FAISS au demarrage de Django"""
      from chatbot.engine.faiss_search  import load_index
      from chatbot.engine.tfidf_fallback import load as load_tfidf
      load_index()
      load_tfidf()
 
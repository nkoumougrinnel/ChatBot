from django.apps import AppConfig

<<<<<<< HEAD

class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'
=======
class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'
    
    def ready(self):
        """Initialise les composants du chatbot au démarrage de Django"""
        from chatbot.engine.faiss_search import load_index
        from chatbot.engine.llm_client_persistent import init_session, check_availability
        from chatbot.engine.prompt_builder import build_system_prompt

        from chatbot.engine.embedder import encode  # pour précharger le modèle d'embeddings
        
        # Charger les index
        load_index()
        
        # Initialiser la session LLM persistante
        try:
            # Vérifier que Ollama est disponible
            status = check_availability()
            if status["available"]:
                system_prompt = build_system_prompt()
                init_session(system_prompt)
                print("[ChatbotConfig] ✓ Session LLM initialisée avec succès")
                encode("Test")  # Précharger le modèle d'embeddings
            else:
                print(f"[ChatbotConfig] ⚠ Ollama non disponible : {status['error']}")
        except Exception as e:
            print(f"[ChatbotConfig] ✗ Erreur init LLM session : {e}")
>>>>>>> 63bc96bc834531acd7719edd6e3541982a2ed93e

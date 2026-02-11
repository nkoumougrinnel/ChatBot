
import os

from django.apps import AppConfig


class FaqConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'faq'

    def ready(self):
        """
        Initialiser le vectorizer TF-IDF au démarrage de Django.
        
        Cela garantit que le vectorizer est entraîné et disponible
        pour tous les requests API (et non seulement dans le shell).
        """
        
        """
        Note: Cette méthode est appelée deux fois par StatReloader.
        On utilise une variable d'environnement pour éviter les appels redondants.
        """
        # Éviter d'initialiser deux fois à cause du StatReloader
        if os.environ.get('_FAQ_VECTORIZER_INITIALIZED'):
            return
        
        os.environ['_FAQ_VECTORIZER_INITIALIZED'] = '1'
        
        try:
            from chatbot.vectorization import compute_and_store_vectors
            print("[FAQ] Initialisation du vectorizer TF-IDF...")
            compute_and_store_vectors()
            print("[FAQ] ✓ Vectorizer entraîné et FAQVectors stockés en BD")
        except Exception as e:
            print(f"[FAQ] ⚠ Initialisation vectorizer échouée : {e}")
            print("[FAQ] Le chatbot ne fonctionnera pas tant que ce problème n'est pas résolu")
        
        # ===== Importer les signaux =====
        try:
            from faq import signals
            print("[FAQ] ✓ Signaux d'amélioration des scores chargés")
        except Exception as e:
            print(f"[FAQ] ⚠ Erreur lors du chargement des signaux : {e}")

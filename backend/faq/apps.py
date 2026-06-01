<<<<<<< HEAD
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
        try:
            from chatbot.vectorization import compute_and_store_vectors
            print("[FAQ] Initialisation du vectorizer TF-IDF...")
            compute_and_store_vectors()
            print("[FAQ] ✓ Vectorizer entraîné et FAQVectors stockés en BD")
        except Exception as e:
            print(f"[FAQ] ⚠ Initialisation vectorizer échouée : {e}")
            print("[FAQ] Le chatbot ne fonctionnera pas tant que ce problème n'est pas résolu")
=======
import os
import sys
import time
from pathlib import Path
from django.apps import AppConfig


# class FaqConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'faq'

#     def ready(self):
#         """
#         Initialiser le vectorizer TF-IDF au démarrage de Django.

#         Version avec logging détaillé pour debug.
#         """
        
#         # ===== DEBUG : Afficher qu'on est bien dans ready() =====
#         print("=" * 80, file=sys.stderr)
#         print("[FAQ DEBUG] ready() appelé !", file=sys.stderr)
#         print(f"[FAQ DEBUG] PID: {os.getpid()}", file=sys.stderr)
#         print(f"[FAQ DEBUG] RUN_MAIN: {os.environ.get('RUN_MAIN')}", file=sys.stderr)
#         print("=" * 80, file=sys.stderr)
        
#         # ===== 1. Protection contre le double-chargement du autoreloader =====
#         # EN PRODUCTION avec Gunicorn, RUN_MAIN n'existe pas, donc on skip cette vérification
#         run_main = os.environ.get('RUN_MAIN')
#         if run_main and run_main != 'true':
#             print("[FAQ] ⏭️ Skip (autoreloader parent process)", file=sys.stderr)
#             return
        
#         # ===== 2. Lock fichier pour éviter l'init multiple avec Gunicorn =====
#         import tempfile
#         temp_dir = Path(tempfile.gettempdir())
#         lock_file = temp_dir / 'faq_vectorizer.lock'
#         init_done_file = temp_dir / 'faq_vectorizer_done.flag'
        
#         print(f"[FAQ DEBUG] Lock file: {lock_file}", file=sys.stderr)
#         print(f"[FAQ DEBUG] Done flag: {init_done_file}", file=sys.stderr)
#         print(f"[FAQ DEBUG] Done flag exists: {init_done_file.exists()}", file=sys.stderr)
        
#         # Si déjà initialisé (flag existe), skip
#         if init_done_file.exists():
#             print("[FAQ] ⏭️ Vectorizer déjà initialisé (flag détecté)")
#         else:
#             # Essayer d'acquérir le lock
#             try:
#                 print("[FAQ DEBUG] Tentative de création du lock...", file=sys.stderr)
#                 # Créer le fichier lock de façon atomique (fail si existe déjà)
#                 fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
#                 os.write(fd, str(os.getpid()).encode())
#                 os.close(fd)
                
#                 print("[FAQ DEBUG] Lock acquis !", file=sys.stderr)
                
#                 # On a le lock, on initialise
#                 try:
#                     from chatbot.vectorization import compute_and_store_vectors
#                     print("[FAQ] 🚀 Initialisation du vectorizer TF-IDF...")
#                     compute_and_store_vectors()
#                     print("[FAQ] ✅ Vectorizer entraîné et FAQVectors stockés en BD")
                    
#                     # Créer le flag "done"
#                     init_done_file.touch()
#                     print("[FAQ DEBUG] Flag 'done' créé", file=sys.stderr)
                    
#                 except Exception as e:
#                     print(f"[FAQ] ⚠️ Initialisation vectorizer échouée : {e}")
#                     print(f"[FAQ DEBUG] Exception complète:", file=sys.stderr)
#                     import traceback
#                     traceback.print_exc()
#                 finally:
#                     # Libérer le lock
#                     lock_file.unlink(missing_ok=True)
#                     print("[FAQ DEBUG] Lock libéré", file=sys.stderr)
                    
#             except FileExistsError:
#                 # Un autre worker a le lock, attendre qu'il finisse
#                 print("[FAQ] ⏳ Attente de l'initialisation par un autre worker...")
#                 print(f"[FAQ DEBUG] Lock déjà pris, attente...", file=sys.stderr)
                
#                 # Attendre max 60 secondes que le flag "done" apparaisse
#                 for i in range(60):
#                     if init_done_file.exists():
#                         print("[FAQ] ✅ Initialisation terminée par un autre worker")
#                         break
#                     if i % 5 == 0:
#                         print(f"[FAQ DEBUG] Attente... {i}s", file=sys.stderr)
#                     time.sleep(1)
#                 else:
#                     # Timeout : nettoyer le lock qui pourrait être bloqué
#                     print("[FAQ] ⚠️ Timeout d'attente - nettoyage du lock")
#                     lock_file.unlink(missing_ok=True)
        
#         # ===== 3. Importer les signaux (chaque worker doit les charger) =====
#         try:
#             from faq import signals
#             print("[FAQ] ✅ Signaux d'amélioration des scores chargés")
#         except Exception as e:
#             print(f"[FAQ] ⚠️ Erreur lors du chargement des signaux : {e}")
#             import traceback
#             traceback.print_exc()
        
#         print("[FAQ DEBUG] ready() terminé", file=sys.stderr)
        
>>>>>>> 63bc96bc834531acd7719edd6e3541982a2ed93e

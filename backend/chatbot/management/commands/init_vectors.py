from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Entraine le vectorizer TF-IDF et stocke les FAQVectors en base.'

    def handle(self, *args, **options):
        try:
            from chatbot.vectorization import compute_and_store_vectors
            self.stdout.write('[FAQ] Lancement de l\'initialisation du vectorizer TF-IDF...')
            compute_and_store_vectors()
            self.stdout.write(self.style.SUCCESS('[FAQ] ✓ Vectorizer entraîné et FAQVectors stockés en BD'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'[FAQ] Erreur lors de l\'initialisation: {e}'))

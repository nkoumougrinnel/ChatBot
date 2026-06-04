"""Initialise la base avec les fixtures de démo et les vecteurs TF-IDF."""

from django.core.management import call_command
from django.core.management.base import BaseCommand

from faq.models import FAQ
from faq.vectorizer_cache import rebuild_faq_vectors


class Command(BaseCommand):
    help = "Migrations + fixtures FAQ de démo + index TF-IDF (prêt pour le frontend React)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-fixtures',
            action='store_true',
            help='Ne pas recharger les fixtures (uniquement reconstruire les vecteurs).',
        )

    def handle(self, *args, **options):
        self.stdout.write("Application des migrations…")
        call_command('migrate', verbosity=0)

        if not options['skip_fixtures']:
            self.stdout.write("Chargement des fixtures FAQ…")
            call_command(
                'loaddata',
                'faq/fixtures/categories.json',
                'faq/fixtures/faq.json',
                verbosity=0,
            )

        faq_count = FAQ.objects.filter(is_active=True).count()
        if faq_count == 0:
            self.stdout.write(self.style.WARNING("Aucune FAQ en base — vectorizer ignoré."))
            return

        self.stdout.write(f"Indexation TF-IDF ({faq_count} FAQs)…")
        vector_count = rebuild_faq_vectors()
        self.stdout.write(self.style.SUCCESS(
            f"Backend pret : {faq_count} FAQs, {vector_count} vecteurs."
        ))
        self.stdout.write("  API : http://127.0.0.1:8000/api/health/")
        self.stdout.write("  Gen3 RAG : python manage.py setup_gen3")
        self.stdout.write("  Frontend React : http://127.0.0.1:5173")

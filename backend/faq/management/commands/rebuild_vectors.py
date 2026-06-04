"""Recalcule les vecteurs TF-IDF après ajout/modification de FAQs."""

from django.core.management.base import BaseCommand

from faq.vectorizer_cache import rebuild_faq_vectors


class Command(BaseCommand):
    help = "Réentraîne le vectorizer TF-IDF et recalcule les FAQVector en base."

    def handle(self, *args, **options):
        count = rebuild_faq_vectors()
        self.stdout.write(self.style.SUCCESS(f"{count} vecteur(s) FAQ recalcule(s)."))

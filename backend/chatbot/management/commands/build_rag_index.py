"""
Construit l'index FAISS Gen3 et le cache TF-IDF fallback.

Usage:
    python manage.py build_rag_index
    python manage.py build_rag_index --rebuild-tfidf
    python manage.py build_rag_index --max-entries 500   # test rapide
"""

import os

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Construit rag_data/index.bin + metadata.json pour le pipeline RAG Gen3."

    def add_arguments(self, parser):
        parser.add_argument(
            "--max-entries",
            type=int,
            default=None,
            help="Limite le nombre de vecteurs (tests rapides).",
        )
        parser.add_argument(
            "--rebuild-tfidf",
            action="store_true",
            help="Reconstruit aussi le cache TF-IDF Gen3 (tfidf_cache.pkl).",
        )
        parser.add_argument(
            "--skip-django",
            action="store_true",
            help="N'inclut pas les FAQs de la base Django.",
        )
        parser.add_argument(
            "--allow-download",
            action="store_true",
            help="Autorise le telechargement du modele MiniLM si absent (HF_OFFLINE=0).",
        )

    def handle(self, *args, **options):
        if options["allow_download"]:
            os.environ["HF_OFFLINE"] = "0"
            os.environ["TRANSFORMERS_OFFLINE"] = "0"

        self.stdout.write("Construction de l'index FAISS Gen3...")
        from chatbot.rag_index_builder import build_rag_index

        stats = build_rag_index(
            max_entries=options["max_entries"],
            include_django=not options["skip_django"],
        )
        self.stdout.write(self.style.SUCCESS(
            f"Index FAISS : {stats['vectors']} vecteurs, dim={stats['dim']}"
        ))

        if options["rebuild_tfidf"]:
            self.stdout.write("Reconstruction du cache TF-IDF Gen3...")
            from chatbot.engine import tfidf_fallback
            from pathlib import Path

            data_dirs = [
                Path(__file__).resolve().parents[3].parent / "data",
                Path(__file__).resolve().parents[3] / "data" / "json",
            ]
            for d in data_dirs:
                if d.is_dir():
                    tfidf_fallback.rebuild(d)
                    break
            else:
                tfidf_fallback.rebuild()
            self.stdout.write(self.style.SUCCESS("Cache TF-IDF Gen3 pret."))

        self.stdout.write("")
        self.stdout.write("Redemarrez Django : python manage.py runserver 127.0.0.1:8001")
        self.stdout.write("Test : GET /api/v2/chatbot/status/")
        if not os.environ.get("GEMINI_API_KEY"):
            self.stdout.write(self.style.WARNING(
                "GEMINI_API_KEY non definie — niveaux CONV/DIRECT/TFIDF actifs, LLM desactive."
            ))

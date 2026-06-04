"""
Initialise tout le stack Gen3 : demo Phase 1 + index FAISS + cache TF-IDF.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Setup demo (Phase 1) + build_rag_index + rebuild TF-IDF Gen3."

    def add_arguments(self, parser):
        parser.add_argument(
            "--allow-download",
            action="store_true",
            help="Telecharge le modele MiniLM si necessaire.",
        )
        parser.add_argument(
            "--max-entries",
            type=int,
            default=None,
            help="Limite les vecteurs FAISS (tests).",
        )

    def handle(self, *args, **options):
        self.stdout.write("=== Phase 1 (Django FAQ + TF-IDF) ===")
        call_command("setup_demo")

        self.stdout.write("\n=== Gen3 (FAISS + embeddings) ===")
        rag_args = ["build_rag_index", "--rebuild-tfidf"]
        if options["allow_download"]:
            rag_args.append("--allow-download")
        if options["max_entries"]:
            rag_args.extend(["--max-entries", str(options["max_entries"])])
        call_command(*rag_args)

        self.stdout.write("\n=== Diagnostic Gen3 ===")
        call_command("check_gen3")

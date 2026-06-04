"""Importe les FAQ depuis le JSON standard et reconstruit les index."""

import subprocess
import sys
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Importe data/supptic_chatbot_standard.json (ou --file), "
        "puis rebuild_vectors et build_rag_index."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='',
            help='Chemin vers le fichier JSON (défaut: data/supptic_chatbot_standard.json).',
        )
        parser.add_argument(
            '--skip-rag',
            action='store_true',
            help='Ne pas reconstruire l index FAISS Gen3.',
        )
        parser.add_argument(
            '--allow-download',
            action='store_true',
            help='Autorise le telechargement du modele embeddings pour FAISS.',
        )

    def handle(self, *args, **options):
        backend = Path(__file__).resolve().parents[3]
        script = backend / 'data' / 'scripts' / 'load_json_data.py'
        if not script.exists():
            self.stderr.write(self.style.ERROR(f'Script introuvable : {script}'))
            return

        self.stdout.write(
            'Import JSON depuis backend/data/json/*.json '
            '(placez vos fichiers JSON dans ce dossier).'
        )
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(backend),
            check=False,
        )
        if result.returncode != 0:
            self.stderr.write(self.style.ERROR('Echec import JSON.'))
            return

        self.stdout.write('Reconstruction vecteurs Phase 1…')
        call_command('rebuild_vectors')

        if not options['skip_rag']:
            self.stdout.write('Reconstruction index RAG Gen3…')
            rag_args = ['build_rag_index', '--rebuild-tfidf']
            if options['allow_download']:
                rag_args.append('--allow-download')
            call_command(*rag_args)

        self.stdout.write(self.style.SUCCESS('Import et indexation termines.'))

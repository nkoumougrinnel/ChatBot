import argparse
import json
import os
import sys
from pathlib import Path

# Configurer Django depuis le dossier backend
ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / 'backend'
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('SKIP_FAQ_VECTORIZER', '1')

import django
from django.db import transaction

django.setup()

from django.apps import apps
Category = apps.get_model('faq', 'Category')
FAQ = apps.get_model('faq', 'FAQ')


def normalize_string(text):
    if not isinstance(text, str):
        return ''
    return ' '.join(text.strip().split())


def build_source_meta(sources, json_id):
    if isinstance(sources, list):
        sources = '; '.join(str(item).strip() for item in sources if item)
    elif sources is None:
        sources = ''
    else:
        sources = str(sources).strip()

    tag = f'[json_id:{json_id}]'
    if sources:
        return f'{sources} {tag}'
    return tag


def faq_exists_by_json_id(json_id):
    tag = f'[json_id:{json_id}]'
    return FAQ.objects.filter(source__contains=tag).first()


def get_or_create_category(name):
    normalized = normalize_string(name)
    if not normalized:
        normalized = 'Non catégorisé'

    category = Category.objects.filter(name__iexact=normalized).first()
    if category:
        return category

    category = Category.objects.create(
        name=normalized,
        description=f'Questions sur {normalized.lower()}',
        active=True,
    )
    print(f'  + Nouvelle catégorie créée: {normalized}')
    return category


class JSONImporter:
    def __init__(self, json_path, dry_run=False):
        self.json_path = Path(json_path)
        self.dry_run = dry_run
        self.stats = {
            'total': 0,
            'imported': 0,
            'skipped_duplicate_id': 0,
            'errors': 0,
        }
        self.seen_ids = set()

    def load_json(self):
        if not self.json_path.exists():
            raise FileNotFoundError(f'Fichier non trouvé: {self.json_path}')

        with self.json_path.open('r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError('Le JSON doit contenir une liste d objets.')

        self.stats['total'] = len(data)
        return data

    def normalize_item(self, item):
        return {
            'id': str(item.get('id', '')).strip(),
            'question': normalize_string(item.get('question', '')),
            'answer': normalize_string(item.get('reponse_enrichie', item.get('answer', ''))),
            'category': normalize_string(item.get('categorie', item.get('category', ''))),
            'subtheme': normalize_string(item.get('sous_theme', item.get('sub_theme', item.get('subtheme', '')))),
            'sources': item.get('sources', []),
        }

    def import_item(self, data):
        json_id = data['id']
        if not json_id:
            raise ValueError('Identifiant JSON manquant pour une entrée.')

        if json_id in self.seen_ids:
            self.stats['skipped_duplicate_id'] += 1
            return

        self.seen_ids.add(json_id)

        existing = faq_exists_by_json_id(json_id)
        if existing:
            self.stats['skipped_duplicate_id'] += 1
            return

        category = get_or_create_category(data['category'])
        source_text = build_source_meta(data['sources'], json_id)

        if self.dry_run:
            self.stats['imported'] += 1
            print(f'[DRY-RUN] Importer FAQ id={json_id} question="{data["question"][:60]}..."')
            return

        FAQ.objects.create(
            question=data['question'],
            answer=data['answer'],
            category=category,
            subtheme=data['subtheme'],
            source=source_text,
            is_active=True,
            popularity=0,
        )
        self.stats['imported'] += 1

    def run(self):
        data = self.load_json()

        with transaction.atomic():
            for item in data:
                try:
                    normalized = self.normalize_item(item)
                    self.import_item(normalized)
                except Exception as exc:
                    self.stats['errors'] += 1
                    print(f'ERREUR sur id={item.get("id")} : {exc}')

        print('\nRésumé de l import:')
        print(f'  Total Lignes : {self.stats["total"]}')
        print(f'  Importées : {self.stats["imported"]}')
        print(f'  Ignorées (id dupliqué) : {self.stats["skipped_duplicate_id"]}')
        print(f'  Erreurs : {self.stats["errors"]}')


def main():
    parser = argparse.ArgumentParser(description='Importer un fichier JSON en base Django (ignorant les doublons par id).')
    parser.add_argument('--file', required=True, help='Chemin du fichier JSON à importer')
    parser.add_argument('--dry-run', action='store_true', help='Ne rien écrire en base, afficher le plan d import.')
    args = parser.parse_args()

    importer = JSONImporter(args.file, dry_run=args.dry_run)
    importer.run()


if __name__ == '__main__':
    main()

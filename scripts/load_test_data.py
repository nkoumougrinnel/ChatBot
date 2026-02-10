"""Script utilitaire pour charger des données de test dans la base Django.

Usage (depuis la racine du dépôt, avec le venv activé) :

powershell:
    python scripts/load_test_data.py

Ce script :
- tente de charger les fixtures Django si elles existent (nommées faq.json, categories.json)
- lit `data/csv/example.csv` si présent et crée `Category` et `FAQ`
- appelle `compute_and_store_vectors()` pour (ré)générer les FAQVectors

Le script est idempotent (utilise get_or_create).
"""
import os
import sys
import csv
import json
from pathlib import Path

# Configurer Django
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
# Prevent apps.ready() from initializing the vectorizer when running this loader
os.environ.setdefault('SKIP_FAQ_VECTORIZER', '1')

import django
from django.core.management import call_command
from django.db import transaction

django.setup()

# Import models via django.apps to avoid import-time issues and be robust
from django.apps import apps
Category = apps.get_model('faq', 'Category')
FAQ = apps.get_model('faq', 'FAQ')

FIXTURES = [
    str(ROOT / 'backend' / 'faq' / 'fixtures' / 'categories.json'),
    str(ROOT / 'backend' / 'faq' / 'fixtures' / 'faq.json'),
]
CSV_PATH = ROOT / 'data' / 'csv' / 'example.csv'


def clear_database():
    """Vider les tables FAQ et Category avant l'import.

    Attention: opération destructive, irréversible.
    """
    print('Clearing database...')
    faq_count = FAQ.objects.all().count()
    cat_count = Category.objects.all().count()
    FAQ.objects.all().delete()
    Category.objects.all().delete()
    print(f"  ✓ Deleted {faq_count} FAQs and {cat_count} Categories")


def try_load_fixtures():
    loaded = False
    for fx in FIXTURES:
        if os.path.exists(fx):
            print(f"Loading fixture: {fx}")
            try:
                call_command('loaddata', fx)
                print(f"  ✓ Loaded {fx}")
                loaded = True
            except Exception as e:
                print(f"  ⚠ Error loading {fx}: {e}")
                # Fallback: try to parse the fixture file as JSON and create objects
                try:
                    parse_json_fixture(fx)
                    loaded = True
                except Exception as e2:
                    print(f"  ⚠ Fallback parsing failed for {fx}: {e2}")
    if not loaded:
        print("No fixtures found or none loaded.")


def parse_json_fixture(fx_path: str):
    """Parse a Django JSON fixture and create corresponding Category/FAQ objects.

    This intentionally supports legacy fixtures that may use different model
    identifiers or field names (e.g., 'faq.categorie', 'categorie', 'reponse').
    """
    print(f"  -> Parsing JSON fixture fallback: {fx_path}")
    with open(fx_path, encoding='utf-8') as fh:
        data = json.load(fh)
    created_counts = {'categories': 0, 'faqs': 0}
    for entry in data:
        model = entry.get('model', '').lower()
        fields = entry.get('fields', {})

        # Category-like models
        if model.endswith('categorie') or model.endswith('category'):
            # try common name fields
            name = fields.get('name') or fields.get('nom') or fields.get('titre') or fields.get('categorie')
            if not name:
                print('    - Skipping category with no name')
                continue
            obj, created = Category.objects.get_or_create(name=name)
            if created:
                created_counts['categories'] += 1

        # FAQ-like models
        elif model.endswith('faq') or model.endswith('question') or model.endswith('qa'):
            question = fields.get('question') or fields.get('titre') or fields.get('q')
            answer = fields.get('answer') or fields.get('reponse') or fields.get('response') or ''
            cat_field = fields.get('category') or fields.get('categorie') or None

            if not question:
                print('    - Skipping FAQ with no question')
                continue

            # Resolve category: if string, use as name; if numeric, ignore and use Uncategorized
            if isinstance(cat_field, str) and cat_field:
                category, _ = Category.objects.get_or_create(name=cat_field)
            else:
                category, _ = Category.objects.get_or_create(name='Uncategorized')

            obj, created = FAQ.objects.get_or_create(
                question=question,
                defaults={
                    'answer': answer,
                    'category': category,
                }
            )
            if created:
                created_counts['faqs'] += 1
        else:
            # Unknown model: ignore
            continue

    print(f"    -> Created categories: {created_counts['categories']}, faqs: {created_counts['faqs']}")


def import_csv(csv_path: Path):
    if not csv_path.exists():
        # fallback: search for any CSV under data/ recursively
        candidates = list(ROOT.glob('data/**/*.csv'))
        if candidates:
            csv_path = candidates[0]
            print(f"CSV file not found at initial path; using found CSV: {csv_path}")
        else:
            print(f"CSV file not found: {csv_path}")
            return 0

    created = 0
    print(f"Importing CSV: {csv_path}")
    with csv_path.open(newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            # Normalize keys: lower, strip. Some CSVs may produce None keys (malformed header), skip those.
            normalized = {}
            for k, v in row.items():
                if k is None:
                    # skip malformed column with no header
                    continue
                key = k.strip().lower()
                normalized[key] = v.strip() if v is not None else ''
            # Expected column names: category, question, answer, subtheme, source, is_active
            cat_name = normalized.get('category') or normalized.get('categorie') or 'Uncategorized'
            question = normalized.get('question') or normalized.get('question_fr') or normalized.get('q')
            answer = normalized.get('answer') or normalized.get('reponse') or ''
            subtheme = normalized.get('subtheme') or ''
            source = normalized.get('source') or ''
            is_active = normalized.get('is_active', '').lower() in ['1', 'true', 'yes', 'y'] if 'is_active' in normalized else True

            if not question:
                print('  - Skipping row without question')
                continue

            with transaction.atomic():
                category, _ = Category.objects.get_or_create(name=cat_name)
                faq, created_flag = FAQ.objects.get_or_create(
                    question=question,
                    defaults={
                        'answer': answer,
                        'category': category,
                        'subtheme': subtheme,
                        'source': source,
                        'is_active': is_active,
                    }
                )
                if created_flag:
                    created += 1
                    print(f"  + Created FAQ: {question[:60]}")
                else:
                    print(f"  = Exists FAQ: {question[:60]}")
    print(f"Imported {created} new FAQs from CSV")
    return created


if __name__ == '__main__':
    print('=== Load test data script ===')
    clear_database()
    #try_load_fixtures()
    import_csv(CSV_PATH)
    print('=== Done ===')

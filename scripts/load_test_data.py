"""Script utilitaire pour charger des données de test dans la base Django.

Usage (depuis la racine du dépôt, avec le venv activé) :

powershell:
    python scripts/load_test_data.py

Ce script :
- lit tous les fichiers CSV présents dans data/csv (dans tous les sous‑dossiers)
- crée Category et FAQ à partir des données
- appelle compute_and_store_vectors() pour (ré)générer les FAQVectors

Le script est idempotent (utilise get_or_create).
"""
import os
import sys
import csv
from pathlib import Path

# Configurer Django
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
# Prevent apps.ready() from initializing the vectorizer when running this loader
os.environ.setdefault('SKIP_FAQ_VECTORIZER', '1')

import django
from django.db import transaction

django.setup()

# Import models via django.apps
from django.apps import apps
Category = apps.get_model('faq', 'Category')
FAQ = apps.get_model('faq', 'FAQ')


def clear_database():
    """Vider les tables FAQ et Category avant l'import."""
    print('Clearing database...')
    faq_count = FAQ.objects.count()
    cat_count = Category.objects.count()
    FAQ.objects.all().delete()
    Category.objects.all().delete()
    print(f"  ✓ Deleted {faq_count} FAQs and {cat_count} Categories")


def import_csv(csv_path: Path):
    created = 0
    print(f"Importing CSV: {csv_path}")
    with csv_path.open(newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            normalized = { (k.strip().lower() if k else ''): (v.strip() if v else '') for k,v in row.items() if k }
            cat_name = normalized.get('category') or normalized.get('categorie') or 'Uncategorized'
            question = normalized.get('question') or normalized.get('question_fr') or normalized.get('q')
            answer = normalized.get('answer') or normalized.get('reponse') or ''
            subtheme = normalized.get('subtheme') or ''
            source = normalized.get('source') or ''
            is_active = normalized.get('is_active', '').lower() in ['1','true','yes','y'] if 'is_active' in normalized else True

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
    print(f"Imported {created} new FAQs from {csv_path}")
    return created


if __name__ == '__main__':
    print('=== Load test data script ===')
    clear_database()
    # Parcourir tous les CSV dans data/csv et sous‑dossiers
    csv_files = list(ROOT.glob('data/csv/**/*.csv'))
    if not csv_files:
        print("No CSV files found under data/csv/")
    else:
        total_created = 0
        for csv_file in csv_files:
            total_created += import_csv(csv_file)
        print(f"=== Done. Imported {total_created} new FAQs from {len(csv_files)} CSV files ===")

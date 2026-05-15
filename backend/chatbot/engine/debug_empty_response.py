"""Diagnostic pour recherche vide sur /api/chatbot/ask/.

Ce script affiche l'état des données, du vectorizer et des résultats
pour une requête donnée.
"""

import os
import sys
from pathlib import Path

# Assurer l'accès aux modules Django depuis le dossier backend/
ROOT = Path(__file__).resolve().parents[2]  # backend/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from faq.models import FAQ, FAQVector, Category
from chatbot.similarity import find_best_faq, compute_similarity_batch, match_conversational_rule, search_fallback_global, search_by_popularity_with_cache, GOOD_SCORE_THRESHOLD
from chatbot.vectorization import compute_tfidf_vector, load_vectorizer, VECTORIZER_PATH


QUESTION = "Peux t-on etre admis avec un bac litteraire?"
TOP_K = 3


def print_header(title: str):
    print('\n' + '=' * 80)
    print(title)
    print('=' * 80 + '\n')


def show_database_state():
    print_header('État de la base FAQ')
    print('FAQ total:', FAQ.objects.count())
    print('FAQ actives:', FAQ.objects.filter(is_active=True).count())
    print('Categories actives:', Category.objects.filter(active=True).count())
    print('FAQVector total:', FAQVector.objects.count())
    print('FAQVector actives:', FAQVector.objects.filter(faq__is_active=True).count())
    print('Vectorizer pickle exists:', VECTORIZER_PATH.exists(), VECTORIZER_PATH)
    if VECTORIZER_PATH.exists():
        vec = load_vectorizer()
        print('Vectorizer loaded:', vec is not None)
        if vec is not None:
            print('Vectorizer vocab size:', len(vec.vocabulary_))


def show_question_analysis(question: str):
    print_header('Analyse de la question')
    print('Question:', question)
    print('Lower:', question.lower())
    print('Direct conversational rule:', match_conversational_rule(question))
    vector, norm = compute_tfidf_vector(question)
    print('TF-IDF vector shape:', getattr(vector, 'shape', None))
    print('TF-IDF norm:', norm)
    nonzero = int((vector != 0).sum())
    print('TF-IDF non-zero terms:', nonzero)
    if hasattr(vector, 'tolist'):
        print('Example non-zero values:', [v for v in vector.tolist() if v != 0][:10])


def show_search_results(question: str, top_k: int):
    print_header('Recherche find_best_faq')
    results = find_best_faq(question, top_k=top_k)
    print('Résultats count:', len(results))
    for idx, res in enumerate(results, start=1):
        faq = res['faq']
        print(f'{idx}. score={res["score"]:.4f} | FAQ #{faq.id} | category={getattr(faq.category, "name", None)}')
        print('   question:', getattr(faq, 'question', None))
        print('   answer:', getattr(faq, 'answer', None)[:120])


if __name__ == '__main__':
    show_database_state()
    show_question_analysis(QUESTION)
    show_search_results(QUESTION, TOP_K)

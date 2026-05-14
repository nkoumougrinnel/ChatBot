"""
Utilitaires généraux pour l'application chatbot.
Point d'entrée unique pour les fonctions du cœur du chatbot.
"""

from chatbot.preprocessing import preprocess_text, TextPreprocessor
from chatbot.vectorization import (
    train_vectorizer,
    compute_tfidf_vector,
    compute_and_store_vectors,
)
from chatbot.similarity import (
    compute_cosine_similarity,
    find_best_faq,
)

__all__ = [
    'preprocess_text',
    'TextPreprocessor',
    'train_vectorizer',
    'compute_tfidf_vector',
    'compute_and_store_vectors',
    'compute_cosine_similarity',
    'find_best_faq',
]

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

def get_chatbot_response(question: str, top_k: int = 3):
    """
    Trouve les réponses les plus pertinentes pour une question utilisateur.

    Args:
        question (str): La question posée par l'utilisateur.
        top_k (int): Nombre de réponses à retourner.

    Returns:
        dict: Résultats formatés avec les FAQs pertinentes.
    """
    # Étape 1 : Trouver les FAQs les plus pertinentes
    # (find_best_faq attend la question brute : il gère lui-même la
    # vectorisation TF-IDF et les règles conversationnelles).
    faq_results = find_best_faq(question, top_k=top_k)

    # Étape 2 : Déterminer le statut de confiance
    if not faq_results:
        status = "not found"
    elif faq_results[0]["score"] < 0.6:
        status = "not found"
    elif faq_results[0]["score"] < 0.8:
        status = "uncertain"
    else:
        status = "confident"

    # Étape 3 : Formater la réponse
    return {
        "question": question,
        "results": faq_results,
        "count": len(faq_results),
        "status": status,
    }


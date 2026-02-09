"""
Module de calcul de similarité et recherche de FAQs pertinentes.
Utilise la similarité cosinus entre vecteurs TF-IDF.
"""

import numpy as np
from faq.models import FAQ, FAQVector
from chatbot.vectorization import compute_tfidf_vector


def compute_cosine_similarity(vec1, vec2):
    """
    Calcule la similarité cosinus entre deux vecteurs.
    
    Args:
        vec1 (np.ndarray): Premier vecteur (1D)
        vec2 (np.ndarray): Deuxième vecteur (1D)
    
    Returns:
        float: Score de similarité entre 0 et 1
    """
    # Calculer normes et produit scalaire directement (plus rapide que sklearn)
    # Supporte vecteurs 1D numpy
    vec1 = np.asarray(vec1)
    vec2 = np.asarray(vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    score = float(np.dot(vec1, vec2) / (norm1 * norm2))
    # Clip entre 0 et 1 pour éviter flottants hors borne
    return max(0.0, min(1.0, score))


def find_best_faq(question: str, top_k: int = 3):
    """
    Recherche les FAQ les plus pertinentes pour une question donnée.
    
    Pipeline:
    1. Prétraitement et vectorisation de la question utilisateur
    2. Récupération de tous les vecteurs TF-IDF stockés en base
    3. Calcul de la similarité cosinus pour chaque FAQ
    4. Tri par score décroissant et extraction des top_k
    
    Args:
        question (str): Question posée par l'utilisateur
        top_k (int): Nombre de résultats à retourner (défaut: 3)
    
    Returns:
        list[dict]: Liste de dictionnaires {'faq': FAQ, 'score': float}
    """
    # Prétraitement et vectorisation de la question
    user_vec, user_norm = compute_tfidf_vector(question)
    results = []
    
    # Récupération de tous les vecteurs stockés en base
    all_vectors = FAQVector.objects.all()
    for faq_vec in all_vectors:
        # Calcul de la similarité cosinus en utilisant la norme pré-calculée
        faq_vector = np.array(faq_vec.tfidf_vector)
        faq_norm = getattr(faq_vec, 'norm', None)
        if faq_norm is None:
            # Tombe-back: calculer si la norme n'est pas présente
            faq_norm = np.linalg.norm(faq_vector)
        if user_norm == 0 or faq_norm == 0:
            score = 0.0
        else:
            score = float(np.dot(user_vec, faq_vector) / (user_norm * faq_norm))
            score = max(0.0, min(1.0, score))
        results.append({
            'faq': faq_vec.faq,
            'score': score
        })
    
    # Tri par score décroissant et extraction des top_k
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_k]
from chatbot.preprocessing import TextPreprocessor
from chatbot.vectorization import compute_tfidf_vector
from faq.models import FAQ, FAQVector
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def compute_cosine_similarity(vec1, vec2):
    """Calcule la similarité cosinus entre deux vecteurs
    Les vecteurs doivent être remodélés pour scikit-learn(2D array)"""

    #On s'assure que les vecteurs sont au bon format pour le calcul
    v1 = vec1.reshape(1, -1)
    v2 = vec2.reshape(1, -1)

    #Retourne une valeur entre 0 et 1
    return cosine_similarity(v1, v2)[0][0]

def find_best_faq(question, top_k=3):
    """Recherche les FAQ les plus pertinentes pour une question donnée"""
    #1. Prétraitement et vectorisation de la question utilisateur
    #(Utilise le vectoriseur entraîné le matin du Jour 2)
    user_vec = compute_tfidf_vector(question)
    results = []

    #2. Récupération de tous les vecteurs stockés en base (FAQVector)
    all_vectors = FAQVector.objects.all()
    for faq_vec in all_vectors:
        #3. Calcul de la similarité cosinus entre la question et chaque FAQ
        score = compute_cosine_similarity(user_vec, faq_vec.vector_numpy)
        results.append({
            'faq': faq_vec.faq,
            'score': score
        })

        #4. Tri par score décroissant et extraction des top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

def preprocess_text(text: str):
    preproc = TextPreprocessor()
    return preproc.preprocess(text)

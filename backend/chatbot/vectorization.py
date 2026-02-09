"""
Module de tokenisation et vecteur TF-IDF.

Ce module fournit des utilitaires pour entraîner un `TfidfVectorizer`,
calculer le vecteur TF-IDF d'une chaîne de caractères et stocker ces vecteurs
dans le modèle `FAQVector` lié aux instances `FAQ`.

Fonctions principales :
- `train_vectorizer(corpus)` : entraîne le vectorizer sur un corpus de questions.
- `compute_tfidf_vector(text)` : calcule le vecteur TF-IDF et sa norme pour un texte.
- `compute_and_store_vectors()` : calcule et persiste les vecteurs pour toutes les FAQ.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from faq.models import FAQ, FAQVector

# Vectorizer TF-IDF global (initialement non entraîné)
vectorizer = None


def train_vectorizer(corpus):
    """
    Entraîner et mémoriser un `TfidfVectorizer` sur un corpus donné.

    Args:
        corpus (iterable[str]): itérable de documents (questions) servant
            d'ensemble d'entraînement pour le TF-IDF.

    Returns:
        TfidfVectorizer: l'instance entraînée du vectorizer
    """
    global vectorizer
    # Créer un nouveau vectorizer (paramètres par défaut)
    vectorizer = TfidfVectorizer()
    # Ajuster le vectorizer sur le corpus fourni
    vectorizer.fit(corpus)
    return vectorizer


def compute_tfidf_vector(text):
    """
    Calculer le vecteur TF-IDF d'une chaîne de caractères et sa norme euclidienne.

    Args:
        text (str): le texte à transformer en vecteur TF-IDF

    Returns:
        tuple[numpy.ndarray, float]: (vecteur numpy 1D, norme L2 du vecteur)

    Raises:
        ValueError: si le `vectorizer` n'a pas encore été entraîné.
    """
    global vectorizer
    if vectorizer is None:
        # Protéger contre l'utilisation avant entraînement
        raise ValueError("Vectorizer not trained. Call train_vectorizer first.")
    # Transformer le texte en vecteur TF-IDF (format sparse → dense)
    vector = vectorizer.transform([text]).toarray()[0]
    # Calculer la norme L2 (utile pour la similarité cosinus)
    norm = np.linalg.norm(vector)
    return vector, norm


def compute_and_store_vectors():
    """
    Construire un vectorizer à partir de toutes les questions de la base,
    puis calculer et sauvegarder le vecteur TF-IDF pour chaque FAQ.

    Comportement:
    - Récupère le corpus (liste des questions) depuis le modèle `FAQ`.
    - Entraîne le `TfidfVectorizer` sur ce corpus.
    - Pour chaque FAQ, calcule le vecteur et la norme, puis met à jour
      ou crée une instance `FAQVector` liée.
    """
    # Récupérer toutes les questions (itérable de chaînes)
    corpus = FAQ.objects.values_list("question", flat=True)
    # Entraîner le vectorizer sur ce corpus
    train_vectorizer(corpus)

    # Parcourir chaque FAQ et stocker son vecteur TF-IDF
    for faq in FAQ.objects.all():
        # Calculer vecteur et norme pour la question
        vector, norm = compute_tfidf_vector(faq.question)
        # Convertir le vecteur en liste pour le stockage JSON-serializable
        FAQVector.objects.update_or_create(
            faq=faq,
            defaults={
                "tfidf_vector": vector.tolist(),
                "norm": norm,
            },
        )

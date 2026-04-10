"""
Module de tokenisation et vecteur TF-IDF.
<<<<<<< HEAD
=======
VERSION OPTIMISÉE pour corpus de 15000+ FAQs avec 1GB RAM.

Optimisations clés:
1. Vectorizer sauvegardé sur disque (pickle) - chargé une seule fois
2. Limite de features (max_features=3000) pour réduire dimensionnalité
3. Traitement par batch lors de l'initialisation
4. float32 au lieu de float64 partout
>>>>>>> 5d3964364534cdcbb97c8d55151f3aac0b45f482

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
<<<<<<< HEAD
from faq.models import FAQ, FAQVector

# Vectorizer TF-IDF global (initialement non entraîné)
vectorizer = None


def train_vectorizer(corpus):
    """
    Entraîner et mémoriser un `TfidfVectorizer` sur un corpus donné.

=======
import pickle
from pathlib import Path
from faq.models import FAQ, FAQVector

# Chemin pour sauvegarder le vectorizer entraîné
import tempfile
VECTORIZER_PATH = Path(tempfile.gettempdir()) / 'tfidf_vectorizer.pkl'

# Vectorizer TF-IDF global (chargé depuis le disque)
vectorizer = None


def save_vectorizer(vec, path=VECTORIZER_PATH):
    """
    Sauvegarder le vectorizer entraîné sur disque.
    
    Args:
        vec (TfidfVectorizer): Vectorizer entraîné
        path (Path): Chemin de sauvegarde
    """
    try:
        with open(path, 'wb') as f:
            pickle.dump(vec, f)
        print(f"[Vectorization] Vectorizer sauvegardé: {path}")
    except Exception as e:
        print(f"[Vectorization] Erreur sauvegarde: {e}")


def load_vectorizer(path=VECTORIZER_PATH):
    """
    Charger le vectorizer depuis le disque.
    
    Args:
        path (Path): Chemin du fichier pickle
    
    Returns:
        TfidfVectorizer ou None si fichier n'existe pas
    """
    global vectorizer
    
    if path.exists():
        try:
            with open(path, 'rb') as f:
                vectorizer = pickle.load(f)
            print(f"[Vectorization] Vectorizer chargé depuis: {path}")
            return vectorizer
        except Exception as e:
            print(f"[Vectorization] Erreur chargement: {e}")
            return None
    
    return None


def train_vectorizer(corpus):
    """
    Entraîner et mémoriser un `TfidfVectorizer` sur un corpus donné.
    
    OPTIMISATIONS:
    - max_features=5000 : Limite dimensionnalité (au lieu de 5000-10000)
    - norm=None : Pas de normalisation (on le fait manuellement)
    - dtype=np.float32 : Économise 50% de RAM
    
>>>>>>> 5d3964364534cdcbb97c8d55151f3aac0b45f482
    Args:
        corpus (iterable[str]): itérable de documents (questions) servant
            d'ensemble d'entraînement pour le TF-IDF.

    Returns:
        TfidfVectorizer: l'instance entraînée du vectorizer
    """
    global vectorizer
<<<<<<< HEAD
    # Créer un nouveau vectorizer (paramètres par défaut)
    vectorizer = TfidfVectorizer()
    # Ajuster le vectorizer sur le corpus fourni
    vectorizer.fit(corpus)
=======
    
    # OPTIMISATION: Limiter le nombre de features pour réduire la dimensionnalité
    # 3000 features au lieu de tout le vocabulaire = -60% RAM
    vectorizer = TfidfVectorizer(
        norm=None,
        max_features=5000,  # LIMITE CRITIQUE !
        dtype=np.float32     # float32 au lieu de float64
    )
    
    # Ajuster le vectorizer sur le corpus fourni
    print(f"[Vectorization] Entraînement sur {len(corpus)} questions...")
    vectorizer.fit(corpus)
    print(f"[Vectorization] Vocabulaire: {len(vectorizer.vocabulary_)} mots")
    
    # Sauvegarder sur disque pour réutilisation
    save_vectorizer(vectorizer)
    
>>>>>>> 5d3964364534cdcbb97c8d55151f3aac0b45f482
    return vectorizer


def compute_tfidf_vector(text):
    """
    Calculer le vecteur TF-IDF d'une chaîne de caractères et sa norme euclidienne.
<<<<<<< HEAD

=======
    
    OPTIMISATION: Le vectorizer est chargé UNE FOIS depuis le disque au lieu
    d'être rechargé à chaque requête.
    
>>>>>>> 5d3964364534cdcbb97c8d55151f3aac0b45f482
    Args:
        text (str): le texte à transformer en vecteur TF-IDF

    Returns:
<<<<<<< HEAD
        tuple[numpy.ndarray, float]: (vecteur numpy 1D, norme L2 du vecteur)
=======
        tuple[numpy.ndarray, float]: (vecteur numpy 1D float32, norme L2 du vecteur)
>>>>>>> 5d3964364534cdcbb97c8d55151f3aac0b45f482

    Raises:
        ValueError: si le `vectorizer` n'a pas encore été entraîné.
    """
    global vectorizer
<<<<<<< HEAD
    if vectorizer is None:
        # Si le vectorizer n'est pas entraîné, essayer un entraînement à la demande
        # en utilisant le corpus des questions existantes en base. Cela évite
        # d'échouer avec une 500 lorsque l'initialisation n'a pas été faite
        # (par ex. processus séparé). Note: opération coûteuse la première fois.
        try:
            from faq.models import FAQ
=======
    
    # Charger le vectorizer si pas encore fait
    if vectorizer is None:
        vectorizer = load_vectorizer()
        
        # Si toujours pas de vectorizer, essayer de l'entraîner
        if vectorizer is None:
            print("[Vectorization] Vectorizer non trouvé, entraînement à la demande...")
>>>>>>> 5d3964364534cdcbb97c8d55151f3aac0b45f482
            corpus = list(FAQ.objects.values_list('question', flat=True))
            if corpus:
                train_vectorizer(corpus)
            else:
                raise ValueError("Vectorizer not trained and no FAQ corpus available.")
<<<<<<< HEAD
        except Exception:
            raise ValueError("Vectorizer not trained. Call train_vectorizer first.")
    # Transformer le texte en vecteur TF-IDF (format sparse → dense)
    vector = vectorizer.transform([text]).toarray()[0]
    # Calculer la norme L2 (utile pour la similarité cosinus)
    norm = np.linalg.norm(vector)
=======
    
    # Transformer le texte en vecteur TF-IDF (format sparse → dense)
    vector = vectorizer.transform([text]).toarray()[0]
    
    # Calculer la norme L2 (utile pour la similarité cosinus)
    norm = np.linalg.norm(vector)
    
>>>>>>> 5d3964364534cdcbb97c8d55151f3aac0b45f482
    return vector, norm


def compute_and_store_vectors():
    """
    Construire un vectorizer à partir de toutes les questions de la base,
    puis calculer et sauvegarder le vecteur TF-IDF pour chaque FAQ.
<<<<<<< HEAD

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
=======
    
    OPTIMISATION: Traitement par batch de 1000 FAQs pour économiser RAM.
    
    Comportement:
    - Récupère le corpus (liste des questions) depuis le modèle `FAQ`.
    - Entraîne le `TfidfVectorizer` sur ce corpus avec max_features=3000.
    - Pour chaque FAQ (par batch), calcule le vecteur et la norme, puis met à jour
      ou crée une instance `FAQVector` liée.
    """
    # Récupérer toutes les questions (itérable de chaînes)
    print("[Vectorization] Récupération du corpus...")
    corpus = list(FAQ.objects.values_list("question", flat=True))
    
    if not corpus:
        print("[Vectorization] Aucune FAQ en base, skip")
        return
    
    total_faqs = len(corpus)
    print(f"[Vectorization] Corpus: {total_faqs} FAQs")
    
    # Entraîner le vectorizer sur ce corpus
    train_vectorizer(corpus)
    
    # OPTIMISATION: Traiter par batch pour éviter de charger 15000 FAQs en RAM
    batch_size = 1000
    vectors_created = 0
    
    for i in range(0, total_faqs, batch_size):
        # Charger un batch de FAQs
        faqs_batch = FAQ.objects.all()[i:i+batch_size]
        
        # Calculer les vecteurs pour ce batch
        questions_batch = [faq.question for faq in faqs_batch]
        vectors_batch = vectorizer.transform(questions_batch).toarray()
        
        # Sauvegarder les vecteurs
        for idx, faq in enumerate(faqs_batch):
            vector = vectors_batch[idx]
            norm = np.linalg.norm(vector)
            
            # Convertir le vecteur en liste pour le stockage JSON-serializable
            FAQVector.objects.update_or_create(
                faq=faq,
                defaults={
                    "tfidf_vector": vector.tolist(),
                    "norm": float(norm),
                },
            )
            vectors_created += 1
        
        # Afficher la progression
        progress = min(i + batch_size, total_faqs)
        print(f"[Vectorization] Progression: {progress}/{total_faqs} FAQs ({int(progress/total_faqs*100)}%)")
    
    print(f"[Vectorization] ✅ {vectors_created} vecteurs calculés et stockés")
>>>>>>> 5d3964364534cdcbb97c8d55151f3aac0b45f482

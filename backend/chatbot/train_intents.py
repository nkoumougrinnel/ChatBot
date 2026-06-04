"""
Entraînement du classifieur d'intents TF-IDF + Logistic Regression.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline


def train_intent_classifier(intents: list):
    """
    Entraîne un classifieur d'intents.

    Args:
        intents (list): Liste de dicts avec les clés 'intent', 'examples', 'responses'.

    Returns:
        sklearn.pipeline.Pipeline: Modèle entraîné (TF-IDF + LogisticRegression).

    Raises:
        ValueError: Si aucun exemple d'entraînement n'est disponible.
    """
    examples = []
    labels = []

    for intent in intents:
        for example in intent.get("examples", []):
            examples.append(example)
            labels.append(intent["intent"])

    if not examples:
        raise ValueError("Aucun exemple d'entraînement trouvé dans les intents.")

    model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000))
    model.fit(examples, labels)
    return model

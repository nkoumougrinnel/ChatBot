from intents_loader import load_intents
import os
import pickle

def train_intent_classifier(intents):
    """Entraîne un classifieur d'intents."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline

    examples = []
    labels = []

    for intent in intents:
        for example in intent["examples"]:
            examples.append(example)
            labels.append(intent["intent"])

    # Pipeline TF-IDF + Logistic Regression
    model = make_pipeline(TfidfVectorizer(), LogisticRegression())
    model.fit(examples, labels)
    return model

# Charger les intents
intents = load_intents("data/supptic_chatbot_standard.json")

# Entraîner le modèle
intent_model = train_intent_classifier(intents)

# Vérifier et créer le dossier 'models/' si nécessaire
models_dir = "models"
if not os.path.exists(models_dir):
    os.makedirs(models_dir)

# Sauvegarder le modèle entraîné
model_path = os.path.join(models_dir, "intent_classifier.pkl")
with open(model_path, "wb") as f:
    pickle.dump(intent_model, f)

print(f"Modèle d'intents entraîné et sauvegardé dans {model_path}.")
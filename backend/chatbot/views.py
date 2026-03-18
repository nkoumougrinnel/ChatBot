from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.decorators import api_view

from chatbot.intents_loader import load_intents
from chatbot.train_intents import train_intent_classifier
from chatbot.intent_detection import detect_intent
from chatbot.utils import get_chatbot_response

# ─── Singleton : chargement paresseux du modèle d'intents ────────────────────
_intent_model = None
_intents = None


def _get_intent_model():
    """Charge et met en cache le modèle d'intents (une seule fois au démarrage)."""
    global _intent_model, _intents
    if _intent_model is not None:
        return _intent_model, _intents

    # Chercher les fichiers depuis la racine du repo (deux niveaux au-dessus de backend/)
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    repo_root = os.path.dirname(backend_dir)

    json_path = os.path.join(repo_root, 'data', 'supptic_chatbot_standard.json')
    pkl_path = os.path.join(repo_root, 'models', 'intent_classifier.pkl')

    if os.path.exists(json_path):
        _intents = load_intents(json_path)
        _intent_model = train_intent_classifier(_intents)
    elif os.path.exists(pkl_path):
        with open(pkl_path, 'rb') as f:
            _intent_model = pickle.load(f)
        _intents = []
    else:
        _intent_model = None
        _intents = []

    return _intent_model, _intents


@api_view(["POST"])
def ask_chatbot(request):
    """Endpoint pour poser une question au chatbot."""
    user_query = request.data.get("question")
    if not user_query:
        return Response({"error": "La question est vide"}, status=400)

    intent_model, intents = _get_intent_model()

    # Étape 1 : Détection d'intent (si modèle disponible)
    if intent_model is not None and intents:
        try:
            intent, confidence, response = detect_intent(user_query, intent_model, intents)
            if confidence >= 0.8:
                return Response({
                    "question": user_query,
                    "intent": intent,
                    "response": response,
                    "confidence": confidence,
                })
        except Exception:
            pass  # Fallback silencieux vers TF-IDF

    # Étape 2 : Fallback TF-IDF + similarité cosinus
    result = get_chatbot_response(user_query)
    return Response(result)

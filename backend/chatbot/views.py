from rest_framework.response import Response
from rest_framework.decorators import api_view
from intents_loader import load_intents
from train_intents import train_intent_classifier
from intent_detection import detect_intent
from utils import get_chatbot_response


# Charger les intents et entraîner le modèle
intents = load_intents("data/supptic_chatbot_standard.json")
intent_model = train_intent_classifier(intents)

@api_view(["POST"])
def ask_chatbot(request):
    """Endpoint pour poser une question."""
    user_query = request.data.get("question")
    if not user_query:
        return Response({"error": "La question est vide"}, status=400)

    # Étape 1 : Détection d'intent
    intent, confidence, response = detect_intent(user_query, intent_model, intents)
    if confidence >= 0.8:  # Seuil de confiance
        return Response({
            "question": user_query,
            "intent": intent,
            "response": response,
            "confidence": confidence,
        })

    # Étape 2 : Fallback sur la logique actuelle (TF-IDF + similarité cosinus)
    result = get_chatbot_response(user_query)  # Fonction existante
    return Response(result)
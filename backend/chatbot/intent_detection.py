def detect_intent(question, model, intents):
    """Détecte l'intent d'une question utilisateur."""
    intent = model.predict([question])[0]
    confidence = max(model.predict_proba([question])[0])

    # Récupérer la réponse associée
    for item in intents:
        if item["intent"] == intent:
            response = item["responses"][0]
            return intent, confidence, response

    return None, 0, "Désolé, je ne comprends pas votre question."
def apply_confidence_thresholds(faq_object, score):
    """Pour l'ajout du système de confiance
    Seuils : 0.6 et 0.8
    """
    # Seuil critique : inférieur à 0.6
    if score < 0.6:
        return {
            "answer": "Je n'ai pas trouvé de réponse précise à votre question. Pourriez-vous reformuler ?",
            "faq_id": None,
            "confidence_level": "low",
            "score": score
        }
    
    # Seuil intermédiaire : entre 0.6 et 0.8
    elif 0.6 <= score < 0.8:
        return {
            "answer": f"Voici la réponse la plus proche : {faq_object.answer}",
            "faq_id": faq_object.id,
            "confidence_level": "medium",
            "score": score
        }
    
    # Seuil élevé : supérieur ou égal à 0.8
    else:
        return {
            "answer": faq_object.answer,
            "faq_id": faq_object.id,
            "confidence_level": "high",
            "score": score
        }
from django.core.cache import cache
from similarity import find_best_faq

def get_chatbot_response(user_query):
    """Service principal : Gère le 
    cache et les seuils de confiance.
    """
    # 1. Nettoyer la requête pour la clé de cache
    cache_key = f"query_{user_query.strip().lower()}"

    # 2. Vérifier si la réponse est déjà en cache
    cached_response = cache.get(cache_key)
    if cached_response:
        return cached_response
    
    # 3. Si non masquée, effectuer la recherche TF-IDF
    best_faq, score = find_best_faq(user_query)

    # 4. Appliquer la logique de seuil
    if score < 0.6:
        result = {
            "answer": "Je n'ai pas trouvé de réponse précise. Pourriez-vous reformuler?",
            "status": "not found",
            "score": score
        }
    elif 0.6 <= score < 0.8:
        result = {
            "answer": f"Voici la réponse la plus proche  {best_faq.answer}",
            "status": "uncertain",
            "score": score,
            "faq_id": best_faq.id
        }
    else:
        result = {
            "answer": best_faq.answer,
            "status": "confident",
            "score": score,
            "faq_id": best_faq.id
        }
    
    # 5. Stocker le résultat en cache pour 1 heure (3600 secondes)
    cache.set(cache_key, result, 3600)
    return result
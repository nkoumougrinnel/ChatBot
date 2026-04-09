from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services import get_chatbot_response

# Create your views here.
@api_view(['POST'])
def ask_chatbot(request):
    """Vue API qui reçoit la question 
    de l'utilisateur.
    """
    user_query = request.data.get('question')
    if not user_query:
        return Response({"error": "La question est vide"}, status=400)
    
    # On appelle la fonction de service qui gère :
    # 1. Le Cache
    # 2. La recherche TF-IDF
    # 3. Les seuils (0.6 / 0.8)
    result = get_chatbot_response(user_query)
    return Response(result)

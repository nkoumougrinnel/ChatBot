from rest_framework.decorators import api_view
from rest_framework.response import Response
from similarity import find_best_faq
from .services import apply_confidence_thresholds

# Create your views here.
@api_view(['POST'])
def ask_chatbot(request):
    query = request.data.get('question')

    # 1. Recherche de la meilleure FAQ
    best_faq, score = find_best_faq(query)

    # 2. Appel du module de raffinement
    refined_result = apply_confidence_thresholds(best_faq, score)
    return Response(refined_result)

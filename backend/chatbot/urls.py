from django.urls import path

from .views import ask_chatbot, test_llm_latency

urlpatterns = [
    path('chatbot/ask/', ask_chatbot, name='chatbot-ask'),
    path('chatbot/test-llm/', test_llm_latency, name='test-llm-latency'),
]

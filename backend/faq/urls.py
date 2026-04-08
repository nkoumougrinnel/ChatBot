"""
Routing pour l'API FAQ et Chatbot.
<<<<<<< HEAD
=======

Routes enregistrées via DRF router:
- /api/categories/ : GET, POST, PUT, DELETE
- /api/faq/ : GET, POST, PUT, DELETE
- /api/chatbot/ask/ : POST
- /api/feedback/ : GET, POST
>>>>>>> 5d3964364534cdcbb97c8d55151f3aac0b45f482
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from faq.views import (
    CategoryViewSet,
    FAQViewSet,
    ChatbotAskViewSet,
    FeedbackViewSet,
<<<<<<< HEAD
    faq_stats,
    category_stats,
)

router = DefaultRouter()
=======
)

# Initialiser le router DRF
router = DefaultRouter()

# Enregistrer les ViewSets
>>>>>>> 5d3964364534cdcbb97c8d55151f3aac0b45f482
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'faq', FAQViewSet, basename='faq')
router.register(r'feedback', FeedbackViewSet, basename='feedback')
router.register(r'chatbot', ChatbotAskViewSet, basename='chatbot')

<<<<<<< HEAD
urlpatterns = [
    path('', include(router.urls)),
    path('stats/', faq_stats, name='faq-stats'),
    path('stats/categories/', category_stats, name='category-stats'),
=======
# URLs patterns
urlpatterns = [
    path('', include(router.urls)),
    path('stats/', FeedbackViewSet.faq_stats, name='faq-stats'),
    path('stats/categories/', FeedbackViewSet.category_stats, name='category-stats'),
>>>>>>> 5d3964364534cdcbb97c8d55151f3aac0b45f482
]

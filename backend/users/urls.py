"""
users/urls.py — Routes d'authentification SUP'ONE.

Inclure dans config/urls.py :
    path('api/auth/', include('users.urls')),
"""

from django.urls import path
from users.views import login_view, logout_view, me_view

urlpatterns = [
    path("login/",  login_view,  name="auth-login"),
    path("logout/", logout_view, name="auth-logout"),
    path("me/",     me_view,     name="auth-me"),
]

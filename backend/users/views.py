"""
users/views.py — Authentification SUP'ONE.

Endpoints :
    POST /api/auth/login/     → { token, user: { id, username, email, role } }
    POST /api/auth/logout/    → 200 OK
    GET  /api/auth/me/        → { id, username, email, role }

Stratégie : token Django natif (rest_framework.authtoken).
Pas de JWT pour garder zéro dépendance externe supplémentaire.
"""

from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """
    POST /api/auth/login/
    Body : { "username": str, "password": str }

    Retourne :
        200 → { "token": str, "user": { id, username, email, role, first_name } }
        400 → { "error": "Champs requis" }
        401 → { "error": "Identifiants incorrects" }
    """
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "").strip()

    if not username or not password:
        return Response(
            {"error": "Nom d'utilisateur et mot de passe requis."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(request, username=username, password=password)

    if user is None:
        return Response(
            {"error": "Identifiants incorrects. Vérifiez votre nom d'utilisateur et mot de passe."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return Response(
            {"error": "Ce compte est désactivé. Contactez l'administration."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Créer ou récupérer le token d'authentification
    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        "token": token.key,
        "user": {
            "id":         user.id,
            "username":   user.username,
            "email":      user.email,
            "role":       getattr(user, "role", "anonyme"),
            "first_name": user.first_name,
            "last_name":  user.last_name,
        },
    }, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    POST /api/auth/logout/
    Header : Authorization: Token <token>

    Supprime le token → déconnexion effective.
    """
    try:
        request.user.auth_token.delete()
    except Exception:
        pass
    return Response({"message": "Déconnecté avec succès."}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    """
    GET /api/auth/me/
    Header : Authorization: Token <token>

    Retourne les infos de l'utilisateur connecté.
    Utile pour vérifier si le token est encore valide au démarrage de l'app.
    """
    user = request.user
    return Response({
        "id":         user.id,
        "username":   user.username,
        "email":      user.email,
        "role":       getattr(user, "role", "anonyme"),
        "first_name": user.first_name,
        "last_name":  user.last_name,
    })

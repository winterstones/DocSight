"""
SEMAINE 2 — JWT Double Token via HttpOnly Cookies

Le principe senior :
  - React ne stocke JAMAIS les tokens (pas de localStorage, pas de state)
  - Les cookies HttpOnly sont envoyés automatiquement par le navigateur
  - JavaScript ne peut pas lire ces cookies (immunité XSS)
  - Si l'access_token expire → /auth/refresh/ émet un nouveau via le refresh_token
"""
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated

from .serializers import LoginSerializer, UserSerializer, ChangePasswordSerializer


def _set_auth_cookies(response: Response, refresh: RefreshToken) -> Response:
    """
    Pose les deux cookies HttpOnly sur la réponse.
    Appelé à la connexion et au refresh.
    """
    jwt_settings = settings.SIMPLE_JWT

    response.set_cookie(
        key=jwt_settings["AUTH_COOKIE"],
        value=str(refresh.access_token),
        max_age=int(jwt_settings["ACCESS_TOKEN_LIFETIME"].total_seconds()),
        httponly=jwt_settings["AUTH_COOKIE_HTTP_ONLY"],
        secure=jwt_settings["AUTH_COOKIE_SECURE"],
        samesite=jwt_settings["AUTH_COOKIE_SAMESITE"],
    )
    response.set_cookie(
        key=jwt_settings["AUTH_COOKIE_REFRESH"],
        value=str(refresh),
        max_age=int(jwt_settings["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        httponly=jwt_settings["AUTH_COOKIE_HTTP_ONLY"],
        secure=jwt_settings["AUTH_COOKIE_SECURE"],
        samesite=jwt_settings["AUTH_COOKIE_SAMESITE"],
    )
    return response


class LoginView(APIView):
    """
    POST /api/auth/login/
    Body: { "username": "...", "password": "..." }

    Retourne les données utilisateur (pas les tokens — ils sont dans les cookies).
    """
    permission_classes = []  # Public endpoint

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if not user:
            return Response(
                {"error": "Identifiants invalides."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh  = RefreshToken.for_user(user)
        response = Response({"user": UserSerializer(user).data})
        return _set_auth_cookies(response, refresh)


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blackliste le refresh token et supprime les cookies.
    """

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"])

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except (TokenError, InvalidToken):
                pass  # Token déjà expiré ou invalide — on logout quand même

        response = Response({"detail": "Déconnecté avec succès."})
        response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE"])
        response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"])
        return response


class RefreshView(APIView):
    """
    POST /api/auth/refresh/
    Émet un nouvel access_token à partir du refresh_token (cookie HttpOnly).
    Appelé automatiquement par l'intercepteur Axios côté React.
    """
    permission_classes = []

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"])

        if not refresh_token:
            return Response(
                {"error": "Refresh token manquant."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            refresh  = RefreshToken(refresh_token)
            response = Response({"detail": "Token rafraîchi."})
            return _set_auth_cookies(response, refresh)
        except (TokenError, InvalidToken):
            return Response(
                {"error": "Refresh token invalide ou expiré."},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class MeView(APIView):
    """GET /api/auth/me/ — Retourne l'utilisateur connecté (via cookie)."""

    def get(self, request):
        return Response({"user": UserSerializer(request.user).data})


class ChangePasswordView(APIView):
    """
    POST /api/auth/password/change/
    Change le mot de passe de l'utilisateur et blackliste le refresh token actuel.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"error": "Ancien mot de passe incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()

        # Blacklist le refresh token actuel
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"])
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except (TokenError, InvalidToken):
                pass

        response = Response({"detail": "Mot de passe modifié avec succès."})
        response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE"])
        response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"])
        return response

"""
Authentification JWT via cookie HttpOnly.
Lit le token dans le cookie au lieu du header Authorization.
"""
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class CookieJWTAuthentication(JWTAuthentication):
    """
    Surcharge de JWTAuthentication pour lire le token
    depuis le cookie HttpOnly plutôt que le header Authorization.

    React n'envoie jamais le token explicitement —
    le navigateur le joint automatiquement à chaque requête.
    """

    def authenticate(self, request):
        cookie_name = settings.SIMPLE_JWT.get("AUTH_COOKIE", "access_token")
        raw_token   = request.COOKIES.get(cookie_name)

        if raw_token is None:
            return None  # Pas de cookie → requête anonyme

        try:
            validated_token = self.get_validated_token(raw_token)
        except (InvalidToken, TokenError):
            return None  # Token invalide → l'intercepteur Axios fera un refresh

        return self.get_user(validated_token), validated_token

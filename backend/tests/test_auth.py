import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user():
    return User.objects.create_user(username="testuser", password="testpassword123", email="test@example.com")

@pytest.mark.django_db
def test_login_sets_httponly_cookies(api_client, user):
    url = reverse('auth-login')
    response = api_client.post(url, {"username": "testuser", "password": "testpassword123"}, format='json')
    
    assert response.status_code == 200
    assert "user" in response.data
    
    # Check cookies
    access_cookie = response.cookies.get(settings.SIMPLE_JWT["AUTH_COOKIE"])
    refresh_cookie = response.cookies.get(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"])
    
    assert access_cookie is not None
    assert refresh_cookie is not None
    
    assert access_cookie["httponly"] == settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"]
    assert refresh_cookie["httponly"] == settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"]

@pytest.mark.django_db
def test_logout_blacklists_refresh_token(api_client, user):
    # Login first
    login_url = reverse('auth-login')
    response = api_client.post(login_url, {"username": "testuser", "password": "testpassword123"}, format='json')
    
    refresh_token = response.cookies.get(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"]).value
    
    # Logout
    logout_url = reverse('auth-logout')
    api_client.cookies[settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"]] = refresh_token
    logout_response = api_client.post(logout_url)
    
    assert logout_response.status_code == 200
    
    # Check if blacklisted
    with pytest.raises(TokenError):
        token = RefreshToken(refresh_token)
        token.check_blacklist()

@pytest.mark.django_db
def test_refresh_issues_new_access_token(api_client, user):
    # Login first
    login_url = reverse('auth-login')
    response = api_client.post(login_url, {"username": "testuser", "password": "testpassword123"}, format='json')
    
    old_access_token = response.cookies.get(settings.SIMPLE_JWT["AUTH_COOKIE"]).value
    refresh_token = response.cookies.get(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"]).value
    
    # Refresh
    refresh_url = reverse('auth-refresh')
    api_client.cookies[settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"]] = refresh_token
    refresh_response = api_client.post(refresh_url)
    
    assert refresh_response.status_code == 200
    
    new_access_token = refresh_response.cookies.get(settings.SIMPLE_JWT["AUTH_COOKIE"]).value
    assert new_access_token is not None
    assert old_access_token != new_access_token

@pytest.mark.django_db
def test_protected_endpoint_rejects_anonymous(api_client):
    url = reverse('auth-me') # protected endpoint
    response = api_client.get(url)
    
    assert response.status_code == 401

@pytest.mark.django_db
def test_change_password_revokes_session(api_client, user):
    # Login first
    login_url = reverse('auth-login')
    response = api_client.post(login_url, {"username": "testuser", "password": "testpassword123"}, format='json')
    
    access_token = response.cookies.get(settings.SIMPLE_JWT["AUTH_COOKIE"]).value
    refresh_token = response.cookies.get(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"]).value
    
    # Setup the cookie for the authenticated request
    api_client.cookies[settings.SIMPLE_JWT["AUTH_COOKIE"]] = access_token
    api_client.cookies[settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"]] = refresh_token
    
    # Change password
    change_pwd_url = reverse('auth-password-change')
    change_response = api_client.post(change_pwd_url, {
        "old_password": "testpassword123",
        "new_password": "newpassword123"
    }, format='json')
    
    assert change_response.status_code == 200
    
    # Verify cookies are deleted
    assert change_response.cookies.get(settings.SIMPLE_JWT["AUTH_COOKIE"]).value == ""
    assert change_response.cookies.get(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"]).value == ""
    
    # Verify password is changed
    user.refresh_from_db()
    assert user.check_password("newpassword123")
    
    # Verify old refresh token is blacklisted
    with pytest.raises(TokenError):
        token = RefreshToken(refresh_token)
        token.check_blacklist()

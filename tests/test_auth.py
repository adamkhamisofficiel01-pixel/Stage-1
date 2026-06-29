"""Tests — authentification (connexion / déconnexion)."""

import pytest


# ---------------------------------------------------------------------------
# Page de connexion (GET /)
# ---------------------------------------------------------------------------

class TestLoginPage:
    def test_login_page_renders(self, client):
        """La page de connexion doit retourner 200."""
        r = client.get("/")
        assert r.status_code == 200

    def test_login_page_contains_form(self, client):
        html = client.get("/").get_data(as_text=True)
        assert 'name="username"' in html
        assert 'name="password"' in html
        assert 'type="submit"' in html

    def test_login_page_has_logo(self, client):
        html = client.get("/").get_data(as_text=True)
        assert "logo.png" in html

    def test_authenticated_user_redirected_to_dashboard(self, client, as_admin):
        """Un admin déjà connecté qui va sur / doit être redirigé."""
        r = client.get("/")
        assert r.status_code == 302
        assert "/accueil" in r.location or "/dashboard" in r.location


# ---------------------------------------------------------------------------
# POST connexion
# ---------------------------------------------------------------------------

class TestLoginPost:
    def test_wrong_credentials_stay_on_login(self, client):
        """Mauvais identifiants → on reste sur la page de connexion (200)."""
        r = client.post("/", data={"username": "FAUX", "password": "wrong"})
        assert r.status_code == 200
        html = r.get_data(as_text=True)
        assert "incorrect" in html.lower() or "login" in html.lower()

    def test_empty_username_fails(self, client):
        r = client.post("/", data={"username": "", "password": "admin123"})
        assert r.status_code == 200

    def test_empty_password_fails(self, client):
        r = client.post("/", data={"username": "TIJANI TARIK", "password": ""})
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Déconnexion
# ---------------------------------------------------------------------------

class TestLogout:
    def test_logout_redirects_to_login(self, client, as_admin):
        r = client.get("/logout")
        assert r.status_code == 302
        assert "/" in r.location

    def test_logout_unauthenticated_redirects(self, client):
        r = client.get("/logout")
        assert r.status_code == 302

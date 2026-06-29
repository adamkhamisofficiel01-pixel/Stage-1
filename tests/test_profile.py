"""Tests — page de profil."""

import pytest


class TestProfilePage:
    def test_anonymous_redirected(self, client):
        r = client.get("/profile/")
        assert r.status_code == 302

    def test_user_sees_profile(self, client, as_user):
        r = client.get("/profile/")
        assert r.status_code == 200

    def test_admin_sees_profile(self, client, as_admin):
        r = client.get("/profile/")
        assert r.status_code == 200

    def test_profile_shows_pseudo(self, client, as_admin):
        html = client.get("/profile/").get_data(as_text=True)
        assert "TIJANI TARIK" in html

    def test_profile_shows_role_badge(self, client, as_admin):
        html = client.get("/profile/").get_data(as_text=True)
        assert "Administrateur" in html

    def test_profile_shows_update_form(self, client, as_user):
        html = client.get("/profile/").get_data(as_text=True)
        assert 'name="email"' in html
        assert 'name="function"' in html
        assert 'name="current-password"' in html
        assert 'name="new-password"' in html

    def test_profile_shows_privileges_section(self, client, as_user):
        html = client.get("/profile/").get_data(as_text=True)
        assert "Privilèges" in html

    def test_profile_admin_sees_all_privileges(self, client, as_admin):
        html = client.get("/profile/").get_data(as_text=True)
        assert "Admin" in html or "admin" in html.lower()

    def test_profile_initials_displayed(self, client, as_admin):
        html = client.get("/profile/").get_data(as_text=True)
        assert "TT" in html  # TIJANI TARIK -> TT


class TestUpdateProfile:
    def test_anonymous_blocked(self, client):
        r = client.post("/profile/update", data={})
        assert r.status_code == 302

    def test_update_email_and_fonction(self, client, as_user):
        r = client.post("/profile/update", data={
            "email": "nouveau@onda.ma",
            "function": "Contrôleur Senior",
        })
        assert r.status_code == 302
        assert "/profile/" in r.location

    def test_password_change_without_current_pw_fails(self, client, as_user):
        r = client.post("/profile/update", data={
            "new-password": "newpass123",
            "confirm-password": "newpass123",
            "current-password": "",
        }, follow_redirects=True)
        html = r.get_data(as_text=True)
        assert "mot de passe actuel" in html.lower()

    def test_password_mismatch_fails(self, client, as_user):
        r = client.post("/profile/update", data={
            "current-password": "user123",
            "new-password": "abc123",
            "confirm-password": "xyz999",
        }, follow_redirects=True)
        html = r.get_data(as_text=True)
        assert "correspondent pas" in html

    def test_new_password_too_short_fails(self, client, as_user):
        r = client.post("/profile/update", data={
            "current-password": "user123",
            "new-password": "ab",
            "confirm-password": "ab",
        }, follow_redirects=True)
        html = r.get_data(as_text=True)
        assert "6 caractères" in html or "minimum" in html.lower() or "redirect" in str(r.status_code)

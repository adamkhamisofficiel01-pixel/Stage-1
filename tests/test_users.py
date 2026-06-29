"""Tests — gestion des utilisateurs."""

import pytest


# ---------------------------------------------------------------------------
# Accès à la page
# ---------------------------------------------------------------------------

class TestUsersAccess:
    def test_anonymous_blocked(self, client):
        r = client.get("/users/")
        assert r.status_code == 302

    def test_regular_user_forbidden(self, client, as_user):
        r = client.get("/users/")
        assert r.status_code == 403

    def test_user_no_priv_forbidden(self, client, as_user_no_priv):
        r = client.get("/users/")
        assert r.status_code == 403

    def test_admin_can_access(self, client, as_admin):
        r = client.get("/users/")
        assert r.status_code == 200

    def test_page_shows_user_list(self, client, as_admin):
        html = client.get("/users/").get_data(as_text=True)
        # Mock supabase returns 2 users
        assert "TIJANI TARIK" in html or "user-card" in html

    def test_page_has_add_form(self, client, as_admin):
        html = client.get("/users/").get_data(as_text=True)
        assert 'name="pseudo"' in html
        assert 'name="password"' in html

    def test_page_has_edit_modal(self, client, as_admin):
        html = client.get("/users/").get_data(as_text=True)
        assert "edit-modal" in html
        assert "delete-modal" in html


# ---------------------------------------------------------------------------
# Ajout d'utilisateur
# ---------------------------------------------------------------------------

class TestAddUser:
    def test_anonymous_blocked(self, client):
        r = client.post("/users/add", data={})
        assert r.status_code == 302

    def test_regular_user_forbidden(self, client, as_user):
        r = client.post("/users/add", data={})
        assert r.status_code == 403

    def test_missing_pseudo_flashes_error(self, client, as_admin):
        r = client.post("/users/add", data={
            "pseudo": "",
            "password": "test123",
            "confirm-password": "test123",
        }, follow_redirects=True)
        html = r.get_data(as_text=True)
        assert "obligatoires" in html or "obligatoire" in html

    def test_password_mismatch_flashes_error(self, client, as_admin):
        r = client.post("/users/add", data={
            "pseudo": "TEST USER",
            "email": "test@onda.ma",
            "function": "Agent",
            "service": "Direction",
            "password": "abc123",
            "confirm-password": "xyz999",
            "account-type": "user",
        }, follow_redirects=True)
        html = r.get_data(as_text=True)
        assert "correspondent pas" in html

    def test_valid_add_redirects(self, client, as_admin):
        r = client.post("/users/add", data={
            "pseudo": "NOUVEAU AGENT",
            "email": "agent@onda.ma",
            "function": "Agent",
            "service": "Direction",
            "password": "secure123",
            "confirm-password": "secure123",
            "account-type": "user",
        })
        assert r.status_code == 302
        assert "/users/" in r.location


# ---------------------------------------------------------------------------
# Modification d'utilisateur
# ---------------------------------------------------------------------------

class TestEditUser:
    def test_anonymous_blocked(self, client):
        r = client.post("/users/edit/aaaa-aaaa-aaaa-aaaa", data={})
        assert r.status_code == 302

    def test_regular_user_forbidden(self, client, as_user):
        r = client.post("/users/edit/aaaa-aaaa-aaaa-aaaa", data={})
        assert r.status_code == 403

    def test_valid_edit_redirects(self, client, as_admin):
        r = client.post("/users/edit/bbbb-bbbb-bbbb-bbbb", data={
            "pseudo": "BENALI YOUSSEF",
            "email": "y.benali@onda.ma",
            "function": "Contrôleur Senior",
            "service": "Service navigation - control aérien",
            "account-type": "user",
            "privilege": ["download"],
        })
        assert r.status_code == 302

    def test_empty_pseudo_rejected(self, client, as_admin):
        r = client.post("/users/edit/bbbb-bbbb-bbbb-bbbb", data={
            "pseudo": "",
            "account-type": "user",
        }, follow_redirects=True)
        html = r.get_data(as_text=True)
        assert "obligatoire" in html

    def test_password_mismatch_rejected(self, client, as_admin):
        r = client.post("/users/edit/bbbb-bbbb-bbbb-bbbb", data={
            "pseudo": "BENALI YOUSSEF",
            "account-type": "user",
            "password": "newpass",
            "confirm-password": "different",
        }, follow_redirects=True)
        html = r.get_data(as_text=True)
        assert "correspondent pas" in html


# ---------------------------------------------------------------------------
# Suppression d'utilisateur
# ---------------------------------------------------------------------------

class TestDeleteUser:
    def test_anonymous_blocked(self, client):
        r = client.post("/users/delete/bbbb-bbbb-bbbb-bbbb")
        assert r.status_code == 302

    def test_regular_user_forbidden(self, client, as_user):
        r = client.post("/users/delete/bbbb-bbbb-bbbb-bbbb")
        assert r.status_code == 403

    def test_cannot_delete_own_account(self, client, as_admin):
        r = client.post("/users/delete/aaaa-aaaa-aaaa-aaaa",
                        follow_redirects=True)
        html = r.get_data(as_text=True)
        assert "propre compte" in html

    def test_admin_can_delete_other_user(self, client, as_admin):
        r = client.post("/users/delete/bbbb-bbbb-bbbb-bbbb")
        assert r.status_code == 302

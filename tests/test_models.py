"""Tests — modèles et décorateurs d'autorisation."""

import pytest
from app.models import User


# ---------------------------------------------------------------------------
# Modèle User
# ---------------------------------------------------------------------------

class TestUserModel:
    def _make(self, **kwargs):
        base = {
            "id": "test-id",
            "pseudo": "TEST USER",
            "mail": None,
            "fonction": None,
            "service": None,
            "password_hash": "x",
            "role": "user",
            "privileges": [],
        }
        base.update(kwargs)
        return User(base)

    def test_get_id_returns_string(self):
        u = self._make(id=42)
        assert u.get_id() == "42"

    def test_is_admin_true_for_admin_role(self):
        u = self._make(role="admin")
        assert u.is_admin is True

    def test_is_admin_false_for_user_role(self):
        u = self._make(role="user")
        assert u.is_admin is False

    def test_is_authenticated_always_true(self):
        u = self._make()
        assert u.is_authenticated is True

    def test_initials_two_names(self):
        u = self._make(pseudo="TIJANI TARIK")
        assert u.initials == "TT"

    def test_initials_one_name(self):
        u = self._make(pseudo="MONO")
        assert u.initials == "MO"

    def test_initials_three_names_uses_first_two(self):
        u = self._make(pseudo="JEAN PIERRE DUPONT")
        assert u.initials == "JP"

    def test_has_privilege_admin_always_true(self):
        u = self._make(role="admin", privileges=[])
        assert u.has_privilege("download") is True
        assert u.has_privilege("delete") is True
        assert u.has_privilege("nonexistent") is True

    def test_has_privilege_accessall_grants_everything(self):
        u = self._make(role="user", privileges=["accessall"])
        assert u.has_privilege("download") is True
        assert u.has_privilege("delete") is True

    def test_has_privilege_specific_privilege(self):
        u = self._make(role="user", privileges=["download"])
        assert u.has_privilege("download") is True
        assert u.has_privilege("delete") is False
        assert u.has_privilege("add") is False

    def test_has_privilege_multiple_args(self):
        u = self._make(role="user", privileges=["download"])
        # True if ANY of the requested privileges is held
        assert u.has_privilege("download", "add") is True
        assert u.has_privilege("delete", "add") is False

    def test_has_privilege_no_privileges(self):
        u = self._make(role="user", privileges=[])
        assert u.has_privilege("download") is False

    def test_privileges_none_treated_as_empty(self):
        u = self._make(privileges=None)
        assert u.has_privilege("download") is False
        assert u.privileges == []


# ---------------------------------------------------------------------------
# Décorateurs
# ---------------------------------------------------------------------------

class TestAdminRequired:
    def test_admin_can_access(self, client, as_admin):
        r = client.get("/users/")
        assert r.status_code == 200

    def test_user_blocked(self, client, as_user):
        r = client.get("/users/")
        assert r.status_code == 403

    def test_anon_redirected(self, client):
        r = client.get("/users/")
        assert r.status_code == 302


class TestPrivilegeRequired:
    def test_admin_can_add_doc(self, client, as_admin):
        r = client.post("/documents/add", data={
            "doc-title": "T", "doc-code": "X", "doc-date": "2026-01-01",
            "doc-dest": "public",
        })
        assert r.status_code == 302

    def test_user_with_add_priv_can_add(self, client, app):
        """Utilisateur avec seulement 'add' doit pouvoir ajouter un document."""
        from flask_login import login_user, logout_user
        from app.models import User
        user_add = User({
            "id": "dddd", "pseudo": "AGENT ADD", "mail": None,
            "fonction": None, "service": "Direction",
            "password_hash": "x", "role": "user",
            "privileges": ["add"],
        })
        login_user(user_add)
        r = client.post("/documents/add", data={
            "doc-title": "Test", "doc-code": "T01", "doc-date": "2026-01-01",
            "doc-dest": "public",
        })
        assert r.status_code == 302
        logout_user()

    def test_user_without_add_priv_blocked(self, client, as_user):
        r = client.post("/documents/add", data={
            "doc-title": "T", "doc-code": "X", "doc-date": "2026-01-01",
        })
        assert r.status_code == 403

    def test_user_without_delete_priv_blocked(self, client, as_user):
        r = client.post("/documents/delete/d1")
        assert r.status_code == 403

    def test_user_without_download_priv_blocked(self, client, as_user_no_priv):
        r = client.get("/documents/download/d1")
        assert r.status_code == 403

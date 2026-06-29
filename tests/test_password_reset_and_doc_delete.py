"""Tests — mot de passe oublié, réinitialisation, et suppression de
documents depuis l'interface."""

import pytest
from flask_login import login_user, logout_user
from flask_mail import Mail

from app.models import User
from app.mail import generate_reset_token, verify_reset_token


# ---------------------------------------------------------------------------
# Bouton de suppression de document (visible selon privilège)
# ---------------------------------------------------------------------------

class TestDeleteDocumentUI:
    def test_admin_sees_delete_button_on_cards(self, client, as_admin):
        html = client.get("/documents/").get_data(as_text=True)
        assert "confirmDeleteDoc" in html
        assert "btn-dl-danger" in html

    def test_admin_sees_delete_confirmation_modal(self, client, as_admin):
        html = client.get("/documents/").get_data(as_text=True)
        assert "delete-doc-modal" in html

    def test_admin_sees_delete_button_in_detail_modal(self, client, as_admin):
        html = client.get("/documents/").get_data(as_text=True)
        assert "view-doc-delete" in html

    def test_user_with_only_download_does_not_see_delete_button(self, client, as_user):
        html = client.get("/documents/").get_data(as_text=True)
        assert "btn-dl-danger" not in html

    def test_user_with_delete_privilege_sees_delete_button(self, client, app):
        user = User({
            "id": "dddd", "pseudo": "AGENT DELETE", "mail": None,
            "fonction": None, "service": "Direction",
            "password_hash": "x", "role": "user", "privileges": ["delete"],
        })
        login_user(user)
        html = client.get("/documents/").get_data(as_text=True)
        assert "btn-dl-danger" in html
        logout_user()

    def test_delete_route_still_protected_by_privilege(self, client, as_user):
        """'download' alone must not allow deleting via the route either."""
        r = client.post("/documents/delete/d1")
        assert r.status_code == 403

    def test_admin_can_delete_document(self, client, as_admin):
        r = client.post("/documents/delete/d1")
        assert r.status_code == 302


# ---------------------------------------------------------------------------
# Page "Mot de passe oublié"
# ---------------------------------------------------------------------------

class TestForgotPasswordPage:
    def test_page_loads(self, client):
        r = client.get("/forgot-password")
        assert r.status_code == 200

    def test_authenticated_user_redirected(self, client, as_admin):
        r = client.get("/forgot-password")
        assert r.status_code == 302

    def test_page_has_identifier_field(self, client):
        html = client.get("/forgot-password").get_data(as_text=True)
        assert 'name="identifier"' in html

    def test_page_links_back_to_login(self, client):
        html = client.get("/forgot-password").get_data(as_text=True)
        assert "/" in html  # login route


class TestForgotPasswordSubmit:
    def setup_method(self):
        Mail.sent_messages = []

    def test_known_user_with_email_triggers_send(self, client):
        Mail.sent_messages = []
        r = client.post("/forgot-password", data={"identifier": "TIJANI TARIK"},
                        follow_redirects=True)
        assert r.status_code == 200
        assert len(Mail.sent_messages) == 1

    def test_email_contains_reset_link(self, client):
        Mail.sent_messages = []
        client.post("/forgot-password", data={"identifier": "TIJANI TARIK"})
        assert len(Mail.sent_messages) == 1
        assert "reset-password" in Mail.sent_messages[0].body

    def test_unknown_identifier_does_not_send_email(self, client):
        Mail.sent_messages = []
        client.post("/forgot-password", data={"identifier": "PERSONNE INCONNUE"})
        assert len(Mail.sent_messages) == 0

    def test_unknown_identifier_still_shows_generic_success(self, client):
        """Pas d'énumération de comptes : même message que le compte existe ou non."""
        r = client.post("/forgot-password", data={"identifier": "PERSONNE INCONNUE"},
                        follow_redirects=True)
        html = r.get_data(as_text=True)
        assert "compte correspondant" in html.lower()

    def test_empty_identifier_rejected(self, client):
        r = client.post("/forgot-password", data={"identifier": ""})
        assert r.status_code == 200  # re-renders the form with an error


# ---------------------------------------------------------------------------
# Génération / vérification de token
# ---------------------------------------------------------------------------

class TestResetToken:
    def test_token_roundtrip(self):
        token = generate_reset_token("bbbb")
        assert verify_reset_token(token) == "bbbb"

    def test_invalid_token_returns_none(self):
        assert verify_reset_token("not-a-real-token") is None

    def test_tampered_token_returns_none(self):
        token = generate_reset_token("bbbb")
        tampered = token[:-2] + "xx"
        assert verify_reset_token(tampered) is None


# ---------------------------------------------------------------------------
# Page de réinitialisation
# ---------------------------------------------------------------------------

class TestResetPasswordPage:
    def test_valid_token_shows_form(self, client):
        token = generate_reset_token("bbbb")
        r = client.get(f"/reset-password/{token}")
        assert r.status_code == 200
        html = r.get_data(as_text=True)
        assert 'name="password"' in html
        assert 'name="confirm-password"' in html

    def test_invalid_token_redirects_to_forgot_password(self, client):
        r = client.get("/reset-password/garbage-token-value")
        assert r.status_code == 302
        assert "forgot-password" in r.location

    def test_authenticated_user_redirected(self, client, as_admin):
        token = generate_reset_token("bbbb")
        r = client.get(f"/reset-password/{token}")
        assert r.status_code == 302


class TestResetPasswordSubmit:
    def test_password_too_short_rejected(self, client):
        token = generate_reset_token("bbbb")
        r = client.post(f"/reset-password/{token}",
                        data={"password": "ab", "confirm-password": "ab"},
                        follow_redirects=True)
        assert "6 caractères" in r.get_data(as_text=True)

    def test_mismatched_passwords_rejected(self, client):
        token = generate_reset_token("bbbb")
        r = client.post(f"/reset-password/{token}",
                        data={"password": "abcdef", "confirm-password": "xyzxyz"},
                        follow_redirects=True)
        assert "correspondent" in r.get_data(as_text=True)

    def test_valid_reset_redirects_to_login(self, client):
        token = generate_reset_token("bbbb")
        r = client.post(f"/reset-password/{token}",
                        data={"password": "newpass123", "confirm-password": "newpass123"})
        assert r.status_code == 302
        assert r.location.endswith("/")

    def test_invalid_token_on_submit_redirects(self, client):
        r = client.post("/reset-password/garbage-token",
                        data={"password": "abcdef", "confirm-password": "abcdef"})
        assert r.status_code == 302


# ---------------------------------------------------------------------------
# Intégration avec la page de connexion
# ---------------------------------------------------------------------------

class TestLoginPageForgotLink:
    def test_login_links_to_real_forgot_password_route(self, client):
        html = client.get("/").get_data(as_text=True)
        assert "/forgot-password" in html


# ---------------------------------------------------------------------------
# Documents récents cliquables sur la page d'accueil
# ---------------------------------------------------------------------------

class TestHomeClickableDocuments:
    def test_home_page_has_clickable_rows(self, client, as_admin):
        html = client.get("/accueil").get_data(as_text=True)
        assert "clickable-doc-row" in html
        assert "viewDocFromHome" in html

    def test_home_page_has_detail_modal(self, client, as_admin):
        html = client.get("/accueil").get_data(as_text=True)
        assert "view-doc-modal" in html

    def test_home_rows_carry_document_data(self, client, as_admin):
        html = client.get("/accueil").get_data(as_text=True)
        assert "data-info=" in html

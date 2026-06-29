"""Tests — page d'accueil / tableau de bord."""

import pytest


class TestDashboard:
    def test_anonymous_redirected(self, client):
        """Un utilisateur non connecté doit être redirigé vers /."""
        for path in ("/accueil", "/dashboard"):
            r = client.get(path)
            assert r.status_code == 302, f"Expected 302 for {path}"
            assert "/" in r.location

    def test_admin_sees_dashboard(self, client, as_admin):
        r = client.get("/accueil")
        assert r.status_code == 200

    def test_user_sees_dashboard(self, client, as_user):
        r = client.get("/accueil")
        assert r.status_code == 200

    def test_dashboard_contains_airport_name(self, client, as_admin):
        html = client.get("/accueil").get_data(as_text=True)
        assert "Essaouira" in html

    def test_dashboard_contains_tabs(self, client, as_admin):
        html = client.get("/accueil").get_data(as_text=True)
        assert "Présentation" in html
        assert "Fiche Technique" in html
        assert "Compagnies" in html

    def test_dashboard_has_documents_panel(self, client, as_admin):
        html = client.get("/accueil").get_data(as_text=True)
        assert "documents" in html.lower()

    def test_dashboard_has_sidebar_links(self, client, as_admin):
        html = client.get("/accueil").get_data(as_text=True)
        assert "/documents/" in html
        assert "/chat/" in html

    def test_dashboard_redirects_both_paths(self, client, as_user):
        for path in ("/accueil", "/dashboard"):
            r = client.get(path)
            assert r.status_code == 200, f"Expected 200 for {path}"

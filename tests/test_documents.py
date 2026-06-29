"""Tests — bibliothèque documentaire."""

import io
import pytest


# ---------------------------------------------------------------------------
# Accès à la liste des documents
# ---------------------------------------------------------------------------

class TestDocumentsList:
    def test_anonymous_redirected(self, client):
        r = client.get("/documents/")
        assert r.status_code == 302

    def test_admin_sees_list(self, client, as_admin):
        r = client.get("/documents/")
        assert r.status_code == 200

    def test_user_sees_list(self, client, as_user):
        r = client.get("/documents/")
        assert r.status_code == 200

    def test_user_no_priv_sees_list(self, client, as_user_no_priv):
        """Même sans privilèges, la liste est visible (filtrée)."""
        r = client.get("/documents/")
        assert r.status_code == 200

    def test_page_contains_doc_grid(self, client, as_admin):
        html = client.get("/documents/").get_data(as_text=True)
        assert "doc-grid" in html

    def test_admin_sees_add_tab(self, client, as_admin):
        html = client.get("/documents/").get_data(as_text=True)
        assert "add-docc" in html

    def test_user_without_add_priv_no_add_tab(self, client, as_user):
        """Un utilisateur sans privilège 'add' ne voit pas l'onglet Ajouter."""
        html = client.get("/documents/").get_data(as_text=True)
        # The tab button triggers switchTab1 to 'add-docc'
        assert "add-docc" not in html

    def test_doc_cards_rendered(self, client, as_admin):
        html = client.get("/documents/").get_data(as_text=True)
        assert "doc-card" in html

    def test_search_input_present(self, client, as_admin):
        html = client.get("/documents/").get_data(as_text=True)
        assert 'id="search-doc"' in html

    def test_service_filter_present(self, client, as_admin):
        html = client.get("/documents/").get_data(as_text=True)
        assert 'id="service-filter"' in html


# ---------------------------------------------------------------------------
# Ajout d'un document
# ---------------------------------------------------------------------------

class TestAddDocument:
    def test_anonymous_redirected(self, client):
        r = client.post("/documents/add", data={})
        assert r.status_code == 302

    def test_user_without_add_priv_forbidden(self, client, as_user):
        """'download' seul ne donne pas le droit d'ajouter."""
        r = client.post("/documents/add", data={
            "doc-title": "Test", "doc-code": "T-01", "doc-date": "2026-01-01",
        })
        assert r.status_code == 403

    def test_missing_title_flashes_error(self, client, as_admin):
        r = client.post("/documents/add", data={
            "doc-title": "", "doc-code": "T-01", "doc-date": "2026-01-01",
        }, follow_redirects=True)
        html = r.get_data(as_text=True)
        assert "obligatoires" in html

    def test_missing_code_flashes_error(self, client, as_admin):
        r = client.post("/documents/add", data={
            "doc-title": "Test", "doc-code": "", "doc-date": "2026-01-01",
        }, follow_redirects=True)
        html = r.get_data(as_text=True)
        assert "obligatoires" in html

    def test_valid_add_no_file_redirects(self, client, as_admin):
        r = client.post("/documents/add", data={
            "doc-title": "Rapport Test",
            "doc-code": "DOC-999",
            "doc-date": "2026-06-15",
            "doc-type": "numerique",
            "doc-pilote": "P0R01",
            "doc-fournisseur": "Direction",
            "doc-dest": "public",
            "doc-class": "Armoire Z",
        })
        assert r.status_code == 302
        assert "/documents/" in r.location

    def test_invalid_file_type_rejected(self, client, as_admin):
        data = {
            "doc-title": "Test",
            "doc-code": "DOC-998",
            "doc-date": "2026-06-15",
            "doc-dest": "public",
        }
        # Simulate uploading a .exe file
        data["doc-file"] = (io.BytesIO(b"fake exe content"), "virus.exe")
        r = client.post("/documents/add", data=data,
                        content_type="multipart/form-data",
                        follow_redirects=True)
        html = r.get_data(as_text=True)
        assert "autorisé" in html or "format" in html.lower()

    def test_valid_pdf_upload_redirects(self, client, as_admin):
        data = {
            "doc-title": "Test PDF",
            "doc-code": "DOC-997",
            "doc-date": "2026-06-15",
            "doc-dest": "public",
            "doc-file": (io.BytesIO(b"%PDF-1.4 fake"), "report.pdf"),
        }
        r = client.post("/documents/add", data=data,
                        content_type="multipart/form-data")
        assert r.status_code == 302


# ---------------------------------------------------------------------------
# Téléchargement
# ---------------------------------------------------------------------------

class TestDownloadDocument:
    def test_anonymous_redirected(self, client):
        r = client.get("/documents/download/d1")
        assert r.status_code == 302

    def test_user_without_download_priv_forbidden(self, client, as_user_no_priv):
        r = client.get("/documents/download/d1")
        assert r.status_code == 403

    def test_user_with_download_priv_gets_redirect(self, client, as_user):
        """L'utilisateur avec 'download' doit obtenir une redirection vers
        l'URL signée (302) pour un document qui lui est visible (public)."""
        r = client.get("/documents/download/d1")
        assert r.status_code == 302

    def test_admin_can_download(self, client, as_admin):
        r = client.get("/documents/download/d1")
        assert r.status_code == 302


# ---------------------------------------------------------------------------
# Suppression
# ---------------------------------------------------------------------------

class TestDeleteDocument:
    def test_anonymous_redirected(self, client):
        r = client.post("/documents/delete/d1")
        assert r.status_code == 302

    def test_user_without_delete_priv_forbidden(self, client, as_user):
        r = client.post("/documents/delete/d1")
        assert r.status_code == 403

    def test_admin_can_delete(self, client, as_admin):
        r = client.post("/documents/delete/d1")
        assert r.status_code == 302


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

class TestDocumentUtils:
    def test_file_type_by_extension(self):
        from app.documents.utils import file_type_for_filename, FILE_TYPE_BY_EXT
        assert file_type_for_filename("rapport.pdf") == "pdf"
        assert file_type_for_filename("tableau.xlsx") == "xls"
        assert file_type_for_filename("note.docx") == "doc"
        assert file_type_for_filename("pres.pptx") == "ppt"
        assert file_type_for_filename("unknown.zzz") == "pdf"  # default

    def test_file_icon_suffix_mapping(self):
        from app.documents.utils import FILE_ICON_SUFFIX
        assert FILE_ICON_SUFFIX["pdf"] == "pdf"
        assert FILE_ICON_SUFFIX["doc"] == "word"
        assert FILE_ICON_SUFFIX["xls"] == "excel"
        assert FILE_ICON_SUFFIX["ppt"] == "powerpoint"

    def test_allowed_extensions(self):
        from app.documents.utils import ALLOWED_EXTENSIONS
        for ext in ("pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx"):
            assert ext in ALLOWED_EXTENSIONS
        assert "exe" not in ALLOWED_EXTENSIONS
        assert "zip" not in ALLOWED_EXTENSIONS

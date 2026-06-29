"""
conftest.py — fixtures partagées pour tous les tests du projet.

Utilise des mocks légers pour flask_login, flask_wtf et supabase afin
de pouvoir tourner hors réseau, sans installation de paquets tiers.
"""

import os
import sys
import pytest

# ── Inject mocks before importing the app ───────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "mocks"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("SUPABASE_URL",         "https://mock.supabase.co")
os.environ.setdefault("SUPABASE_KEY",          "anon-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY",  "service-key")
os.environ.setdefault("FLASK_SECRET_KEY",      "test-secret-key")

from flask_login import login_user, logout_user, _state          # type: ignore
from app import create_app
from app.models import User

# ---------------------------------------------------------------------------
# Sample user data
# ---------------------------------------------------------------------------
ADMIN_DATA = {
    "id": "aaaa",
    "pseudo": "TIJANI TARIK",
    "mail": "tarik@onda.ma",
    "fonction": "Directeur",
    "service": "Direction",
    "password_hash": "scrypt:32768:8:1$TYfMPAxCxkC0qX75$0f1d956147418eb39b9f0593082db72403275178d81b2f77bd7f491f3f7d97f4c81221113e7898be5c193947e420e2bab78c5dcea53e9da5d9d485427ba982c8",
    "role": "admin",
    "privileges": ["download", "add", "delete", "accessall"],
}

USER_DATA = {
    "id": "bbbb",
    "pseudo": "BENALI YOUSSEF",
    "mail": "youssef@onda.ma",
    "fonction": "Contrôleur Aérien",
    "service": "Service navigation - control aérien",
    "password_hash": "scrypt:32768:8:1$Mba4i0zIqH22kkp9$e52e76af4f5867a19b1c846de67e79fbf7236a51d212b3ee1b14345e8fb6b8582f253e41e0eb4ce5d73489833cca5af3a42c318f18eb880eb066be09dbc7b258",
    "role": "user",
    "privileges": ["download"],
}

USER_NO_PRIV_DATA = {
    "id": "cccc",
    "pseudo": "HADDAD SARA",
    "mail": "sara@onda.ma",
    "fonction": "Technicienne",
    "service": "Service Technique navigation - CNS",
    "password_hash": "x",
    "role": "user",
    "privileges": [],
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app():
    application = create_app()
    application.config.update({"TESTING": True, "WTF_CSRF_ENABLED": False})
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def as_admin(app):
    """Log in as admin, yield, then log out."""
    login_user(User(ADMIN_DATA))
    yield
    logout_user()


@pytest.fixture()
def as_user(app):
    """Log in as a regular user with 'download' privilege."""
    login_user(User(USER_DATA))
    yield
    logout_user()


@pytest.fixture()
def as_user_no_priv(app):
    """Log in as a user with no privileges."""
    login_user(User(USER_NO_PRIV_DATA))
    yield
    logout_user()

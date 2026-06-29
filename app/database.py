"""
Centralised Supabase client access.

Two clients are exposed:
- get_db()         -> anon key client (kept for completeness / future
                       client-side-style queries that should respect RLS)
- get_service_db() -> service-role key client (bypasses RLS). All
                       server-side business logic in this app uses this
                       client because Flask itself is the trusted
                       authorization layer (sessions + decorators).

Both clients are created lazily and cached so we don't reconnect on
every request.
"""

import os
from supabase import create_client, Client

_anon_client: Client | None = None
_service_client: Client | None = None


def get_db() -> Client:
    """Anon-key client (subject to Row Level Security policies)."""
    global _anon_client
    if _anon_client is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        _anon_client = create_client(url, key)
    return _anon_client


def get_service_db() -> Client:
    """Service-role client (bypasses RLS) — server-side use only."""
    global _service_client
    if _service_client is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        _service_client = create_client(url, key)
    return _service_client

"""
Lightweight Flask-Login user wrapper around a row of the `users` table.

We don't use an ORM — Supabase rows come back as plain dicts, and this
class just gives convenient attribute access plus the methods
Flask-Login expects (via UserMixin).
"""

from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, data: dict):
        self.id = data["id"]
        self.pseudo = data.get("pseudo", "")
        self.mail = data.get("mail")
        self.fonction = data.get("fonction")
        self.service = data.get("service")
        self.role = data.get("role", "user")
        self.privileges = data.get("privileges") or []
        self.password_hash = data.get("password_hash")

    # Flask-Login requires get_id() to return a string
    def get_id(self):
        return str(self.id)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def initials(self) -> str:
        parts = [p for p in self.pseudo.split() if p]
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[1][0]).upper()

    def has_privilege(self, *privileges) -> bool:
        """True if the user is admin, has 'accessall', or holds any of
        the given privileges."""
        if self.is_admin:
            return True
        user_privs = set(self.privileges or [])
        if "accessall" in user_privs:
            return True
        return bool(user_privs.intersection(privileges))

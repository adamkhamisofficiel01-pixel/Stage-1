"""
Email sending (Flask-Mail) and password-reset token helpers.

Tokens are generated with itsdangerous' URLSafeTimedSerializer, signed
with the app's FLASK_SECRET_KEY. This avoids needing a dedicated
database table: the token itself embeds the user id and an expiry,
and tampering is detected by signature verification.
"""

import os
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

mail = Mail()

RESET_SALT = "password-reset-salt"
RESET_MAX_AGE_SECONDS = 60 * 60  # 1 hour


def _serializer():
    secret = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")
    return URLSafeTimedSerializer(secret)


def generate_reset_token(user_id: str) -> str:
    """Create a signed, time-limited token embedding the user id."""
    return _serializer().dumps({"user_id": str(user_id)}, salt=RESET_SALT)


def verify_reset_token(token: str):
    """Return the user_id encoded in the token, or None if the token
    is invalid, tampered with, or expired (> RESET_MAX_AGE_SECONDS)."""
    try:
        data = _serializer().loads(token, salt=RESET_SALT, max_age=RESET_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    return data.get("user_id")


def send_reset_email(to_email: str, pseudo: str, reset_url: str):
    """Send the password-reset email. Raises on SMTP failure so the
    caller can decide how to react (flash message, logging, etc.)."""
    subject = "Réinitialisation de votre mot de passe — ONDA Essaouira"

    text_body = (
        f"Bonjour {pseudo},\n\n"
        "Vous avez demandé la réinitialisation de votre mot de passe sur "
        "l'intranet de l'Aéroport Essaouira-Mogador.\n\n"
        f"Cliquez sur le lien suivant pour choisir un nouveau mot de passe "
        f"(valable 1 heure) :\n{reset_url}\n\n"
        "Si vous n'êtes pas à l'origine de cette demande, ignorez simplement "
        "cet email : votre mot de passe actuel reste inchangé.\n\n"
        "— Intranet ONDA Essaouira-Mogador"
    )

    html_body = f"""
    <div style="font-family:Arial,sans-serif;background:#0a1628;padding:32px;color:#f0f4ff;">
      <div style="max-width:480px;margin:0 auto;background:#0f2040;border:1px solid #1a56a0;border-radius:12px;overflow:hidden;">
        <div style="background:#007bff;height:6px;"></div>
        <div style="padding:28px;">
          <h2 style="margin:0 0 16px;color:#ffffff;">Réinitialisation de mot de passe</h2>
          <p>Bonjour <b>{pseudo}</b>,</p>
          <p>Vous avez demandé la réinitialisation de votre mot de passe sur
             l'intranet de l'Aéroport Essaouira-Mogador.</p>
          <p style="text-align:center;margin:28px 0;">
            <a href="{reset_url}" style="background:#007bff;color:white;text-decoration:none;
               padding:12px 28px;border-radius:8px;font-weight:bold;display:inline-block;">
               Choisir un nouveau mot de passe
            </a>
          </p>
          <p style="font-size:13px;color:#a0aec0;">
            Ce lien est valable <b>1 heure</b>. Si vous n'êtes pas à l'origine de cette
            demande, ignorez cet email : votre mot de passe actuel reste inchangé.
          </p>
        </div>
      </div>
    </div>
    """

    msg = Message(subject=subject, recipients=[to_email], body=text_body, html=html_body)
    mail.send(msg)

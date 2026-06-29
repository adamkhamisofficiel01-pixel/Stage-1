from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from ..database import get_service_db
from ..models import User
from ..mail import generate_reset_token, verify_reset_token, send_reset_email

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        pseudo = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        remember = bool(request.form.get("remember-me"))

        if not pseudo or not password:
            flash("Veuillez renseigner votre nom d'utilisateur et votre mot de passe.", "danger")
            return render_template("index.html")

        db = get_service_db()
        res = db.table("users").select("*").eq("pseudo", pseudo).limit(1).execute()
        rows = res.data or []

        if rows and check_password_hash(rows[0]["password_hash"], password):
            user = User(rows[0])
            login_user(user, remember=remember)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))

        flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")

    return render_template("index.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Vous avez été déconnecté.", "success")
    return redirect(url_for("auth.login"))


# ─────────────────────────────────────────────────────────────
# Mot de passe oublié
# ─────────────────────────────────────────────────────────────

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        identifier = (request.form.get("identifier") or "").strip()

        if not identifier:
            flash("Veuillez renseigner votre pseudo ou votre email.", "danger")
            return render_template("forgot_password.html")

        db = get_service_db()
        # Accept either the pseudo or the email address as identifier
        res = (
            db.table("users")
            .select("*")
            .or_(f"pseudo.eq.{identifier},mail.eq.{identifier}")
            .limit(1)
            .execute()
        )
        rows = res.data or []

        # Always show the same confirmation message, whether or not the
        # account exists or has an email on file — this avoids leaking
        # which pseudos/emails are registered (user enumeration).
        if rows and rows[0].get("mail"):
            user = rows[0]
            token = generate_reset_token(user["id"])
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            try:
                send_reset_email(user["mail"], user["pseudo"], reset_url)
            except Exception:
                # Don't reveal SMTP/config errors to the end user; an
                # administrator should check server logs for delivery issues.
                flash(
                    "Une erreur est survenue lors de l'envoi de l'email. "
                    "Veuillez réessayer plus tard ou contacter un administrateur.",
                    "danger",
                )
                return render_template("forgot_password.html")

        flash(
            "Si un compte correspondant existe et possède une adresse email, "
            "un lien de réinitialisation vient de lui être envoyé.",
            "success",
        )
        return redirect(url_for("auth.login"))

    return render_template("forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    user_id = verify_reset_token(token)
    if not user_id:
        flash("Ce lien de réinitialisation est invalide ou a expiré. Veuillez en redemander un.", "danger")
        return redirect(url_for("auth.forgot_password"))

    db = get_service_db()
    res = db.table("users").select("id, pseudo").eq("id", user_id).limit(1).execute()
    rows = res.data or []
    if not rows:
        flash("Ce compte n'existe plus.", "danger")
        return redirect(url_for("auth.forgot_password"))

    pseudo = rows[0]["pseudo"]

    if request.method == "POST":
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm-password") or ""

        if len(password) < 6:
            flash("Le mot de passe doit comporter au moins 6 caractères.", "danger")
            return render_template("reset_password.html", token=token, pseudo=pseudo)

        if password != confirm:
            flash("Les mots de passe ne correspondent pas.", "danger")
            return render_template("reset_password.html", token=token, pseudo=pseudo)

        db.table("users").update({"password_hash": generate_password_hash(password)}) \
            .eq("id", user_id).execute()

        flash("Votre mot de passe a été réinitialisé avec succès. Vous pouvez maintenant vous connecter.", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", token=token, pseudo=pseudo)

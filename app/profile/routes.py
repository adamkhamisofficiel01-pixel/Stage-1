from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from ..database import get_service_db

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.route("/")
@login_required
def view_profile():
    return render_template("profile.html")


@profile_bp.route("/update", methods=["POST"])
@login_required
def update_profile():
    db = get_service_db()

    mail = (request.form.get("email") or "").strip()
    fonction = (request.form.get("function") or "").strip()
    current_pw = request.form.get("current-password") or ""
    new_pw = request.form.get("new-password") or ""
    confirm_pw = request.form.get("confirm-password") or ""

    update_data = {
        "mail": mail or None,
        "fonction": fonction or None,
    }

    # Password change — only if requested
    if new_pw:
        if not current_pw:
            flash("Veuillez saisir votre mot de passe actuel pour le modifier.", "danger")
            return redirect(url_for("profile.view_profile"))

        # Re-fetch hash from DB (current_user object may be stale)
        res = db.table("users").select("password_hash").eq("id", current_user.id).limit(1).execute()
        stored_hash = (res.data or [{}])[0].get("password_hash", "")

        if not check_password_hash(stored_hash, current_pw):
            flash("Mot de passe actuel incorrect.", "danger")
            return redirect(url_for("profile.view_profile"))

        if new_pw != confirm_pw:
            flash("Les nouveaux mots de passe ne correspondent pas.", "danger")
            return redirect(url_for("profile.view_profile"))

        if len(new_pw) < 6:
            flash("Le nouveau mot de passe doit comporter au moins 6 caractères.", "danger")
            return redirect(url_for("profile.view_profile"))

        update_data["password_hash"] = generate_password_hash(new_pw)

    db.table("users").update(update_data).eq("id", current_user.id).execute()
    flash("Profil mis à jour avec succès.", "success")
    return redirect(url_for("profile.view_profile"))

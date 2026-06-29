from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash

from ..database import get_service_db
from ..decorators import admin_required

users_bp = Blueprint("users", __name__, url_prefix="/users")


@users_bp.route("/")
@login_required
@admin_required
def list_users():
    db = get_service_db()
    res = db.table("users").select("*").order("pseudo").execute()
    users = res.data or []
    for u in users:
        parts = [p for p in u["pseudo"].split() if p]
        u["initials"] = (parts[0][0] + parts[1][0]).upper() if len(parts) >= 2 else (parts[0][:2].upper() if parts else "?")
    return render_template("users.html", users=users)


@users_bp.route("/add", methods=["POST"])
@login_required
@admin_required
def add_user():
    db = get_service_db()

    pseudo = (request.form.get("pseudo") or "").strip()
    mail = (request.form.get("email") or "").strip()
    fonction = (request.form.get("function") or "").strip()
    service = request.form.get("service")
    password = request.form.get("password") or ""
    confirm = request.form.get("confirm-password") or ""
    role = request.form.get("account-type", "user")
    privileges = request.form.getlist("privilege")

    if not pseudo or not password:
        flash("Le pseudo et le mot de passe sont obligatoires.", "danger")
        return redirect(url_for("users.list_users"))

    if password != confirm:
        flash("Les mots de passe ne correspondent pas.", "danger")
        return redirect(url_for("users.list_users"))

    existing = db.table("users").select("id").eq("pseudo", pseudo).execute()
    if existing.data:
        flash(f"Le pseudo « {pseudo} » est déjà utilisé.", "danger")
        return redirect(url_for("users.list_users"))

    new_user = {
        "pseudo": pseudo,
        "mail": mail or None,
        "fonction": fonction or None,
        "service": service,
        "password_hash": generate_password_hash(password),
        "role": role if role in ("user", "admin") else "user",
        "privileges": privileges,
    }

    db.table("users").insert(new_user).execute()
    flash(f"Utilisateur « {pseudo} » ajouté avec succès.", "success")
    return redirect(url_for("users.list_users"))


@users_bp.route("/edit/<user_id>", methods=["POST"])
@login_required
@admin_required
def edit_user(user_id):
    db = get_service_db()

    res = db.table("users").select("*").eq("id", user_id).limit(1).execute()
    rows = res.data or []
    if not rows:
        flash("Utilisateur introuvable.", "danger")
        return redirect(url_for("users.list_users"))

    pseudo = (request.form.get("pseudo") or "").strip()
    mail = (request.form.get("email") or "").strip()
    fonction = (request.form.get("function") or "").strip()
    service = request.form.get("service")
    role = request.form.get("account-type", "user")
    privileges = request.form.getlist("privilege")
    password = request.form.get("password") or ""
    confirm = request.form.get("confirm-password") or ""

    if not pseudo:
        flash("Le pseudo est obligatoire.", "danger")
        return redirect(url_for("users.list_users"))

    # Check pseudo uniqueness against other users
    existing = db.table("users").select("id").eq("pseudo", pseudo).execute()
    if any(str(r["id"]) != str(user_id) for r in (existing.data or [])):
        flash(f"Le pseudo « {pseudo} » est déjà utilisé par un autre compte.", "danger")
        return redirect(url_for("users.list_users"))

    # Prevent an admin from demoting/locking themselves out by accident
    if str(user_id) == str(current_user.id) and role != "admin":
        flash("Vous ne pouvez pas retirer votre propre rôle administrateur.", "danger")
        return redirect(url_for("users.list_users"))

    update_data = {
        "pseudo": pseudo,
        "mail": mail or None,
        "fonction": fonction or None,
        "service": service,
        "role": role if role in ("user", "admin") else "user",
        "privileges": privileges,
    }

    if password:
        if password != confirm:
            flash("Les mots de passe ne correspondent pas.", "danger")
            return redirect(url_for("users.list_users"))
        update_data["password_hash"] = generate_password_hash(password)

    db.table("users").update(update_data).eq("id", user_id).execute()
    flash(f"Utilisateur « {pseudo} » modifié avec succès.", "success")
    return redirect(url_for("users.list_users"))


@users_bp.route("/delete/<user_id>", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    if str(user_id) == str(current_user.id):
        flash("Vous ne pouvez pas supprimer votre propre compte.", "danger")
        return redirect(url_for("users.list_users"))

    db = get_service_db()
    db.table("users").delete().eq("id", user_id).execute()
    flash("Utilisateur supprimé.", "success")
    return redirect(url_for("users.list_users"))

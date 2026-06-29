import uuid

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, abort
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from ..database import get_service_db
from ..decorators import privilege_required
from .utils import (
    visible_documents_query, file_type_for_filename, ALLOWED_EXTENSIONS,
    STORAGE_BUCKET, FILE_ICON_SUFFIX,
)

documents_bp = Blueprint("documents", __name__, url_prefix="/documents")


@documents_bp.route("/")
@login_required
def list_documents():
    db = get_service_db()
    res = visible_documents_query(db, current_user).order("date", desc=True).execute()
    documents = res.data or []
    for d in documents:
        d["icon_suffix"] = FILE_ICON_SUFFIX.get(d.get("file_type"), "pdf")
    return render_template("documents.html", documents=documents)


@documents_bp.route("/add", methods=["POST"])
@login_required
@privilege_required("add")
def add_document():
    db = get_service_db()

    titre = (request.form.get("doc-title") or "").strip()
    code = (request.form.get("doc-code") or "").strip()
    date = request.form.get("doc-date") or None

    if not titre or not code:
        flash("Le titre et le code du document sont obligatoires.", "danger")
        return redirect(url_for("documents.list_documents"))

    file_path = None
    file_type = "pdf"

    uploaded = request.files.get("doc-file")
    if uploaded and uploaded.filename:
        ext = uploaded.filename.rsplit(".", 1)[-1].lower() if "." in uploaded.filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            flash("Type de fichier non autorisé (formats acceptés : pdf, doc(x), xls(x), ppt(x)).", "danger")
            return redirect(url_for("documents.list_documents"))

        file_type = file_type_for_filename(uploaded.filename)
        storage_name = f"{uuid.uuid4()}_{secure_filename(uploaded.filename)}"

        try:
            db.storage.from_(STORAGE_BUCKET).upload(
                storage_name,
                uploaded.read(),
                {"content-type": uploaded.mimetype or "application/octet-stream"},
            )
            file_path = storage_name
        except Exception as exc:
            flash(f"Le fichier n'a pas pu être téléversé : {exc}", "danger")
            return redirect(url_for("documents.list_documents"))

    new_doc = {
        "code": code,
        "titre": titre,
        "pilote": (request.form.get("doc-pilote") or "").strip(),
        "date": date,
        "type_doc": request.form.get("doc-type", "numerique"),
        "fournisseur": (request.form.get("doc-fournisseur") or "").strip(),
        "destinataire": request.form.get("doc-dest") or "public",
        "classement": (request.form.get("doc-class") or "").strip(),
        "file_path": file_path,
        "file_type": file_type,
        "created_by": current_user.id,
    }

    db.table("documents").insert(new_doc).execute()
    flash(f"Document « {titre} » ajouté avec succès.", "success")
    return redirect(url_for("documents.list_documents"))


@documents_bp.route("/download/<doc_id>")
@login_required
@privilege_required("download")
def download_document(doc_id):
    db = get_service_db()
    res = db.table("documents").select("*").eq("id", doc_id).limit(1).execute()
    rows = res.data or []

    if not rows or not rows[0].get("file_path"):
        flash("Aucun fichier n'est associé à ce document.", "danger")
        return redirect(url_for("documents.list_documents"))

    doc = rows[0]

    # Visibility check for non-privileged-all users
    if not current_user.is_admin and "accessall" not in (current_user.privileges or []):
        if doc.get("destinataire") not in (current_user.service, "public"):
            abort(403)

    try:
        signed = db.storage.from_(STORAGE_BUCKET).create_signed_url(doc["file_path"], 60)
        signed_url = signed.get("signedURL") or signed.get("signedUrl") or signed.get("signed_url")
    except Exception as exc:
        flash(f"Impossible de générer le lien de téléchargement : {exc}", "danger")
        return redirect(url_for("documents.list_documents"))

    if not signed_url:
        flash("Impossible de générer le lien de téléchargement.", "danger")
        return redirect(url_for("documents.list_documents"))

    return redirect(signed_url)


@documents_bp.route("/delete/<doc_id>", methods=["POST"])
@login_required
@privilege_required("delete")
def delete_document(doc_id):
    db = get_service_db()
    res = db.table("documents").select("file_path, titre").eq("id", doc_id).limit(1).execute()
    rows = res.data or []

    if rows and rows[0].get("file_path"):
        try:
            db.storage.from_(STORAGE_BUCKET).remove([rows[0]["file_path"]])
        except Exception:
            pass  # Don't block the DB delete if storage cleanup fails

    db.table("documents").delete().eq("id", doc_id).execute()
    flash("Document supprimé.", "success")
    return redirect(url_for("documents.list_documents"))

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from ..database import get_service_db
from ..documents.utils import visible_documents_query, FILE_ICON_SUFFIX

main_bp = Blueprint("main", __name__)


@main_bp.route("/accueil")
@main_bp.route("/dashboard")
@login_required
def dashboard():
    db = get_service_db()

    # Latest documents the current user is allowed to see, for the
    # "Derniers documents" panel on the home page.
    query = visible_documents_query(db, current_user)
    res = query.order("date", desc=True).limit(8).execute()
    documents = res.data or []
    for d in documents:
        d["icon_suffix"] = FILE_ICON_SUFFIX.get(d.get("file_type"), "pdf")

    return render_template("acceuil.html", documents=documents)

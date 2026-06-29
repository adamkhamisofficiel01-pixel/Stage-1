"""
Shared helpers for the `documents` table.

Visibility rule: a document is visible to a user if
  - the user is admin, OR
  - the user has the 'accessall' privilege, OR
  - the document's `destinataire` matches the user's service, OR
  - the document's `destinataire` is 'public'.
"""

FILE_TYPE_BY_EXT = {
    "pdf": "pdf",
    "doc": "doc",
    "docx": "doc",
    "xls": "xls",
    "xlsx": "xls",
    "ppt": "ppt",
    "pptx": "ppt",
}

# Maps a stored `file_type` (pdf/doc/xls/ppt) to the FontAwesome
# "fa-file-..." icon suffix used in the document cards.
FILE_ICON_SUFFIX = {
    "pdf": "pdf",
    "doc": "word",
    "xls": "excel",
    "ppt": "powerpoint",
}

ALLOWED_EXTENSIONS = set(FILE_TYPE_BY_EXT.keys())

STORAGE_BUCKET = "documents"


def visible_documents_query(db, user):
    """Return a Supabase query builder for documents visible to `user`.

    Caller is responsible for adding `.order(...)`, `.limit(...)`,
    `.execute()`, etc.
    """
    query = db.table("documents").select("*")

    if user.is_admin or "accessall" in (user.privileges or []):
        return query

    return query.in_("destinataire", [user.service, "public"])


def file_type_for_filename(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return FILE_TYPE_BY_EXT.get(ext, "pdf")

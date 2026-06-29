from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from ..database import get_service_db

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


@chat_bp.route("/")
@login_required
def chat_page():
    db = get_service_db()
    res = (
        db.table("users")
        .select("id, pseudo, fonction, service, role")
        .neq("id", current_user.id)
        .order("pseudo")
        .execute()
    )
    contacts = res.data or []

    # Unread message counts per sender, so the contact list can show badges
    unread_res = (
        db.table("messages")
        .select("sender_id")
        .eq("receiver_id", current_user.id)
        .eq("is_read", False)
        .execute()
    )
    unread_counts: dict[str, int] = {}
    for row in unread_res.data or []:
        sid = row["sender_id"]
        unread_counts[sid] = unread_counts.get(sid, 0) + 1

    for c in contacts:
        c["initials"] = "".join(p[0] for p in c["pseudo"].split()[:2]).upper()
        c["unread"] = unread_counts.get(c["id"], 0)

    return render_template("chat.html", contacts=contacts)


@chat_bp.route("/messages/<other_id>")
@login_required
def get_messages(other_id):
    db = get_service_db()

    res = (
        db.table("messages")
        .select("*")
        .or_(
            f"and(sender_id.eq.{current_user.id},receiver_id.eq.{other_id}),"
            f"and(sender_id.eq.{other_id},receiver_id.eq.{current_user.id})"
        )
        .order("created_at")
        .execute()
    )

    # Mark incoming messages from this contact as read
    db.table("messages").update({"is_read": True}) \
        .eq("sender_id", other_id) \
        .eq("receiver_id", current_user.id) \
        .eq("is_read", False) \
        .execute()

    messages = []
    for m in res.data or []:
        messages.append({
            "id": m["id"],
            "content": m["content"],
            "created_at": m["created_at"],
            "mine": m["sender_id"] == current_user.id,
        })

    return jsonify(messages)


@chat_bp.route("/send", methods=["POST"])
@login_required
def send_message():
    data = request.get_json(silent=True) or {}
    receiver_id = data.get("receiver_id")
    content = (data.get("content") or "").strip()

    if not receiver_id or not content:
        return jsonify({"error": "receiver_id and content are required"}), 400

    db = get_service_db()
    res = db.table("messages").insert({
        "sender_id": current_user.id,
        "receiver_id": receiver_id,
        "content": content,
    }).execute()

    row = (res.data or [{}])[0]
    return jsonify({
        "id": row.get("id"),
        "content": content,
        "created_at": row.get("created_at"),
        "mine": True,
    })


@chat_bp.route("/unread")
@login_required
def unread_counts():
    db = get_service_db()
    res = (
        db.table("messages")
        .select("sender_id")
        .eq("receiver_id", current_user.id)
        .eq("is_read", False)
        .execute()
    )
    counts: dict[str, int] = {}
    for row in res.data or []:
        sid = row["sender_id"]
        counts[sid] = counts.get(sid, 0) + 1
    return jsonify(counts)

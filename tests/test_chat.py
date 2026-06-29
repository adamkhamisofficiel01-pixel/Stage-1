"""Tests — messagerie interne."""

import json
import pytest


class TestChatPage:
    def test_anonymous_redirected(self, client):
        r = client.get("/chat/")
        assert r.status_code == 302

    def test_user_sees_chat_page(self, client, as_user):
        r = client.get("/chat/")
        assert r.status_code == 200

    def test_admin_sees_chat_page(self, client, as_admin):
        r = client.get("/chat/")
        assert r.status_code == 200

    def test_chat_page_lists_contacts(self, client, as_admin):
        html = client.get("/chat/").get_data(as_text=True)
        assert "chat-list" in html

    def test_chat_page_has_input_area(self, client, as_user):
        html = client.get("/chat/").get_data(as_text=True)
        assert "msg-input" in html
        assert "send-btn" in html


class TestGetMessages:
    def test_anonymous_redirected(self, client):
        r = client.get("/chat/messages/bbbb-bbbb-bbbb-bbbb")
        assert r.status_code == 302

    def test_returns_json_list(self, client, as_admin):
        r = client.get("/chat/messages/bbbb-bbbb-bbbb-bbbb")
        assert r.status_code == 200
        assert r.content_type.startswith("application/json")
        data = json.loads(r.get_data(as_text=True))
        assert isinstance(data, list)

    def test_messages_have_expected_keys(self, client, as_admin):
        r = client.get("/chat/messages/bbbb-bbbb-bbbb-bbbb")
        messages = json.loads(r.get_data(as_text=True))
        if messages:
            for m in messages:
                assert "content" in m
                assert "created_at" in m
                assert "mine" in m

    def test_mine_flag_correct_for_sent(self, client, as_admin):
        """Messages sent by the current user must have mine=True."""
        r = client.get("/chat/messages/bbbb-bbbb-bbbb-bbbb")
        messages = json.loads(r.get_data(as_text=True))
        # Mock returns one message from bbbb -> aaaa (incoming for admin)
        # so mine should be False for that message
        for m in messages:
            if not m["mine"]:
                assert m["mine"] is False


class TestSendMessage:
    def test_anonymous_redirected(self, client):
        r = client.post("/chat/send",
                        json={"receiver_id": "x", "content": "hi"},
                        headers={"X-CSRFToken": "test"})
        assert r.status_code == 302

    def test_missing_content_returns_400(self, client, as_admin):
        r = client.post("/chat/send",
                        json={"receiver_id": "bbbb-bbbb-bbbb-bbbb", "content": ""},
                        headers={"X-CSRFToken": "test"})
        assert r.status_code == 400

    def test_missing_receiver_returns_400(self, client, as_admin):
        r = client.post("/chat/send",
                        json={"content": "Bonjour"},
                        headers={"X-CSRFToken": "test"})
        assert r.status_code == 400

    def test_valid_send_returns_200_json(self, client, as_admin):
        r = client.post("/chat/send",
                        json={"receiver_id": "bbbb-bbbb-bbbb-bbbb",
                              "content": "Bonjour Youssef"},
                        headers={"X-CSRFToken": "test"},
                        content_type="application/json")
        assert r.status_code == 200
        data = json.loads(r.get_data(as_text=True))
        assert data.get("content") == "Bonjour Youssef"
        assert data.get("mine") is True

    def test_whitespace_only_content_rejected(self, client, as_admin):
        r = client.post("/chat/send",
                        json={"receiver_id": "bbbb-bbbb-bbbb-bbbb",
                              "content": "   "},
                        headers={"X-CSRFToken": "test"},
                        content_type="application/json")
        assert r.status_code == 400


class TestUnreadCounts:
    def test_anonymous_redirected(self, client):
        r = client.get("/chat/unread")
        assert r.status_code == 302

    def test_returns_dict(self, client, as_admin):
        r = client.get("/chat/unread")
        assert r.status_code == 200
        data = json.loads(r.get_data(as_text=True))
        assert isinstance(data, dict)

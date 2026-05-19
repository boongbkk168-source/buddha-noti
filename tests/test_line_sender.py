"""Tests for line_sender module."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.line_sender import LineSendError, _build_image_url, send


def _mock_response(status_code=200, headers=None, json_body=None):
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.headers = headers or {}
    resp.text = json.dumps(json_body) if json_body else ""
    resp.json.return_value = json_body or {}
    return resp


_ENV = {
    "LINE_CHANNEL_ACCESS_TOKEN": "test-token",
    "LINE_GROUP_ID": "C1234567890abcdef",
}


class TestDryRun:

    def test_dry_run_creates_log_file(self, tmp_path):
        with patch("src.line_sender.LOGS_DIR", tmp_path):
            result = send("ทดสอบข้อความ", dry_run=True)
        assert result["status"] == "dry_run"
        log_path = result["log_path"]
        assert log_path.endswith(".json")

        data = json.loads(open(log_path, encoding="utf-8").read())
        assert data["message"] == "ทดสอบข้อความ"
        assert data["dry_run"] is True

    def test_dry_run_with_image_path(self, tmp_path):
        with patch("src.line_sender.LOGS_DIR", tmp_path):
            result = send("ข้อความ", image_path="/fake/image.png", dry_run=True)
        data = json.loads(open(result["log_path"], encoding="utf-8").read())
        assert data["image_path"] == "/fake/image.png"

    @patch.dict(os.environ, {"LINE_GROUP_ID": "C1234567890abcdef"})
    def test_group_id_masked(self, tmp_path):
        with patch("src.line_sender.LOGS_DIR", tmp_path):
            result = send("ข้อความ", dry_run=True)
        data = json.loads(open(result["log_path"], encoding="utf-8").read())
        assert data["target_group_id_masked"] == "****cdef"

    @patch.dict(os.environ, {}, clear=True)
    def test_group_id_not_set(self, tmp_path):
        with patch("src.line_sender.LOGS_DIR", tmp_path):
            result = send("ข้อความ", dry_run=True)
        data = json.loads(open(result["log_path"], encoding="utf-8").read())
        assert data["target_group_id_masked"] == "NOT_SET"


class TestRealSend:

    @patch.dict(os.environ, _ENV)
    @patch("src.line_sender.requests.post")
    def test_success_200(self, mock_post):
        mock_post.return_value = _mock_response(
            200, headers={"x-line-request-id": "req-abc-123"}
        )
        result = send("วันนี้วันพระค่ะ", dry_run=False)
        assert result["status"] == "sent"
        assert result["request_id"] == "req-abc-123"
        assert result["dry_run"] is False
        mock_post.assert_called_once()

    @patch.dict(os.environ, _ENV)
    @patch("src.line_sender.requests.post")
    def test_400_no_retry(self, mock_post):
        mock_post.return_value = _mock_response(
            400, json_body={"message": "The request body has 1 error(s)"}
        )
        with pytest.raises(LineSendError, match="Bad request.*400"):
            send("ข้อความ", dry_run=False)
        assert mock_post.call_count == 1

    @patch.dict(os.environ, _ENV)
    @patch("src.line_sender.requests.post")
    def test_401_invalid_token(self, mock_post):
        mock_post.return_value = _mock_response(
            401, json_body={"message": "Invalid channel access token"}
        )
        with pytest.raises(LineSendError, match="Invalid token.*401"):
            send("ข้อความ", dry_run=False)
        assert mock_post.call_count == 1

    @patch.dict(os.environ, _ENV)
    @patch("src.line_sender.requests.post")
    def test_403_permission_denied(self, mock_post):
        mock_post.return_value = _mock_response(
            403, json_body={"message": "Not authorized"}
        )
        with pytest.raises(LineSendError, match="Bot not in group.*403"):
            send("ข้อความ", dry_run=False)
        assert mock_post.call_count == 1

    @patch.dict(os.environ, _ENV)
    @patch("src.line_sender.time.sleep")
    @patch("src.line_sender.requests.post")
    def test_429_retry_then_success(self, mock_post, mock_sleep):
        mock_post.side_effect = [
            _mock_response(429, json_body={"message": "rate limited"}),
            _mock_response(200, headers={"x-line-request-id": "req-retry-ok"}),
        ]
        result = send("ข้อความ", dry_run=False)
        assert result["status"] == "sent"
        assert result["request_id"] == "req-retry-ok"
        assert mock_post.call_count == 2
        mock_sleep.assert_called_once_with(2)

    @patch.dict(os.environ, _ENV)
    @patch("src.line_sender.time.sleep")
    @patch("src.line_sender.requests.post")
    def test_5xx_all_retries_fail(self, mock_post, mock_sleep):
        mock_post.return_value = _mock_response(
            500, json_body={"message": "internal error"}
        )
        with pytest.raises(LineSendError, match="HTTP 500"):
            send("ข้อความ", dry_run=False)
        assert mock_post.call_count == 3

    @patch.dict(os.environ, _ENV)
    @patch("src.line_sender.time.sleep")
    @patch("src.line_sender.requests.post")
    def test_timeout_all_retries_fail(self, mock_post, mock_sleep):
        mock_post.side_effect = requests.Timeout("timed out")
        with pytest.raises(LineSendError, match="Timeout"):
            send("ข้อความ", dry_run=False)
        assert mock_post.call_count == 3

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_token_raises(self):
        with pytest.raises(LineSendError, match="TOKEN not set"):
            send("ข้อความ", dry_run=False)


class TestImageSupport:

    @patch.dict(os.environ, _ENV)
    @patch("src.line_sender.requests.post")
    def test_send_with_image(self, mock_post):
        """body ต้องมี 2 messages: text + image"""
        mock_post.return_value = _mock_response(
            200, headers={"x-line-request-id": "req-img-ok"}
        )
        result = send(
            "วันนี้วันพระค่ะ",
            image_path="assets/images/red_buddha.png",
            dry_run=False,
        )
        assert result["status"] == "sent"

        call_kwargs = mock_post.call_args
        body = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        messages = body["messages"]
        assert len(messages) == 2
        assert messages[0]["type"] == "text"
        assert messages[1]["type"] == "image"
        assert "originalContentUrl" in messages[1]
        assert "previewImageUrl" in messages[1]
        assert messages[1]["originalContentUrl"].endswith("red_buddha.png")

    @patch.dict(os.environ, _ENV)
    @patch("src.line_sender.requests.post")
    def test_send_without_image(self, mock_post):
        """body ต้องมี 1 message: text only"""
        mock_post.return_value = _mock_response(
            200, headers={"x-line-request-id": "req-txt-ok"}
        )
        result = send("วันนี้วันพระค่ะ", dry_run=False)
        assert result["status"] == "sent"

        call_kwargs = mock_post.call_args
        body = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        messages = body["messages"]
        assert len(messages) == 1
        assert messages[0]["type"] == "text"

    @patch.dict(os.environ, {
        "GITHUB_REPO": "myuser/myrepo",
        "GITHUB_BRANCH": "dev",
    })
    def test_build_image_url(self):
        """URL format ต้องถูก: raw.githubusercontent.com/{repo}/{branch}/assets/images/{file}"""
        url = _build_image_url("some/path/red_buddha.png")
        assert url == (
            "https://raw.githubusercontent.com/"
            "myuser/myrepo/dev/assets/images/red_buddha.png"
        )

    def test_build_image_url_defaults(self):
        """ถ้าไม่ set env ต้องใช้ default repo/branch"""
        env = {k: v for k, v in os.environ.items()
               if k not in ("GITHUB_REPO", "GITHUB_BRANCH")}
        with patch.dict(os.environ, env, clear=True):
            url = _build_image_url("blue_kone.png")
        assert "boongbkk168-source/buddha-noti" in url
        assert "/main/" in url
        assert url.endswith("blue_kone.png")

    def test_dry_run_logs_image_url(self, tmp_path):
        """dry-run log file ต้องมี image_url field"""
        with patch("src.line_sender.LOGS_DIR", tmp_path):
            result = send(
                "ข้อความ",
                image_path="assets/images/green_buddha.png",
                dry_run=True,
            )
        data = json.loads(open(result["log_path"], encoding="utf-8").read())
        assert "image_url" in data
        assert data["image_url"].endswith("green_buddha.png")
        assert "raw.githubusercontent.com" in data["image_url"]

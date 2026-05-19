"""Tests for message_writer module."""

import os
from unittest.mock import MagicMock, patch

import pytest

from src.message_writer import (
    ConfigError,
    _validate,
    _fallback,
    write,
    PREFIXES,
)


def _make_valid_text(notification_type: str, color: str = "เหลือง") -> str:
    prefix = PREFIXES[notification_type]
    return f"{prefix}\nสีมงคลวันนี้คือสี{color}\nขอให้มีความสุขค่ะ"


def _mock_completion(text: str):
    """สร้าง mock ChatCompletion response."""
    message = MagicMock()
    message.content = text
    choice = MagicMock()
    choice.message = message
    usage = MagicMock()
    usage.prompt_tokens = 100
    usage.completion_tokens = 50
    response = MagicMock()
    response.choices = [choice]
    response.usage = usage
    return response


class TestNotificationTypes:

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"})
    @patch("src.message_writer.openai.OpenAI")
    def test_buddha_day(self, mock_cls):
        text = _make_valid_text("buddha_day")
        mock_cls.return_value.chat.completions.create.return_value = _mock_completion(text)
        result = write("buddha_day", "monday", "เหลือง", "2025-01-06")
        assert result.startswith("วันนี้วันพระค่ะ")

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"})
    @patch("src.message_writer.openai.OpenAI")
    def test_buddha_eve(self, mock_cls):
        text = _make_valid_text("buddha_eve")
        mock_cls.return_value.chat.completions.create.return_value = _mock_completion(text)
        result = write("buddha_eve", "sunday", "แดง", "2025-01-05")
        assert result.startswith("พรุ่งนี้วันพระค่ะ")

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"})
    @patch("src.message_writer.openai.OpenAI")
    def test_kone_eve(self, mock_cls):
        text = _make_valid_text("kone_eve")
        mock_cls.return_value.chat.completions.create.return_value = _mock_completion(text)
        result = write("kone_eve", "saturday", "ม่วง", "2025-01-04")
        assert result.startswith("พรุ่งนี้วันโกนค่ะ")


class TestValidation:

    def test_valid_text(self):
        text = "วันนี้วันพระค่ะ\nสีมงคลวันนี้คือสีเหลือง\nขอให้มีความสุขค่ะ"
        assert _validate(text, "buddha_day", "เหลือง") is True

    def test_missing_color(self):
        text = "วันนี้วันพระค่ะ\nขอให้ทุกท่านมีความสุข\nสาธุค่ะ"
        assert _validate(text, "buddha_day", "เหลือง") is False

    def test_wrong_prefix(self):
        text = "พรุ่งนี้วันพระค่ะ\nสีเหลือง\nสาธุค่ะ"
        assert _validate(text, "buddha_day", "เหลือง") is False


class TestRetryAndFallback:

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"})
    @patch("src.message_writer.time.sleep")
    @patch("src.message_writer.openai.OpenAI")
    def test_retry_on_rate_limit(self, mock_cls, mock_sleep):
        import openai as real_openai

        valid_text = _make_valid_text("buddha_day")
        mock_client = mock_cls.return_value
        mock_client.chat.completions.create.side_effect = [
            real_openai.RateLimitError(
                message="rate limited",
                response=MagicMock(status_code=429, headers={}),
                body={"error": {"message": "rate limited", "type": "rate_limit"}},
            ),
            real_openai.RateLimitError(
                message="rate limited",
                response=MagicMock(status_code=429, headers={}),
                body={"error": {"message": "rate limited", "type": "rate_limit"}},
            ),
            _mock_completion(valid_text),
        ]
        result = write("buddha_day", "monday", "เหลือง", "2025-01-06")
        assert result == valid_text
        assert mock_client.chat.completions.create.call_count == 3

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"})
    @patch("src.message_writer.time.sleep")
    @patch("src.message_writer.openai.OpenAI")
    def test_fallback_after_all_retries(self, mock_cls, mock_sleep):
        import openai as real_openai

        mock_client = mock_cls.return_value
        mock_client.chat.completions.create.side_effect = real_openai.RateLimitError(
            message="rate limited",
            response=MagicMock(status_code=429, headers={}),
            body={"error": {"message": "rate limited", "type": "rate_limit"}},
        )
        result = write("buddha_day", "monday", "เหลือง", "2025-01-06")
        assert "วันนี้วันพระค่ะ" in result
        assert "เหลือง" in result

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"})
    @patch("src.message_writer.openai.OpenAI")
    def test_auth_error_no_retry(self, mock_cls):
        import openai as real_openai

        mock_client = mock_cls.return_value
        mock_client.chat.completions.create.side_effect = real_openai.AuthenticationError(
            message="invalid key",
            response=MagicMock(status_code=401, headers={}),
            body={"error": {"message": "invalid key", "type": "auth_error"}},
        )
        result = write("buddha_day", "monday", "เหลือง", "2025-01-06")
        assert "วันนี้วันพระค่ะ" in result
        assert mock_client.chat.completions.create.call_count == 1

    def test_fallback_passes_validation(self):
        for ntype in ["kone_eve", "buddha_eve", "buddha_day"]:
            text = _fallback(ntype, "เหลือง")
            assert _validate(text, ntype, "เหลือง") is True


class TestConfig:

    @patch.dict(os.environ, {}, clear=True)
    def test_no_api_key_raises_config_error(self):
        with pytest.raises(ConfigError):
            write("buddha_day", "monday", "เหลือง", "2025-01-06")


class TestRegeneration:

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"})
    @patch("src.message_writer.openai.OpenAI")
    def test_regenerate_on_invalid(self, mock_cls):
        invalid_text = "ข้อความผิดรูปแบบ ไม่มี prefix ที่ถูกต้อง"
        valid_text = _make_valid_text("buddha_day")
        mock_client = mock_cls.return_value
        mock_client.chat.completions.create.side_effect = [
            _mock_completion(invalid_text),
            _mock_completion(valid_text),
        ]
        result = write("buddha_day", "monday", "เหลือง", "2025-01-06")
        assert result == valid_text
        assert mock_client.chat.completions.create.call_count == 2

"""Tests for orchestrator module."""

import os
from unittest.mock import patch, MagicMock

from src.orchestrator import run


def _mock_calendar(notification_type, weekday="monday", color="เหลือง", date_iso="2025-01-06"):
    return {
        "date": date_iso,
        "weekday": weekday,
        "weekday_color": color,
        "today": {"is_buddha_day": notification_type == "buddha_day", "is_kone_day": False, "lunar_date": None},
        "tomorrow": {"is_buddha_day": notification_type == "buddha_eve", "is_kone_day": False},
        "notification_type": notification_type,
    }


class TestModeMapping:

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"})
    @patch("src.orchestrator.line_sender.send", return_value={"status": "dry_run", "log_path": "/tmp/test.json"})
    @patch("src.orchestrator.image_picker.pick", return_value="/tmp/test.png")
    @patch("src.orchestrator.message_writer.write", return_value="วันนี้วันพระค่ะ\nสีเหลือง\nสาธุค่ะ")
    @patch("src.orchestrator.calendar_checker.check")
    def test_buddha_day_morning_sent(self, mock_cal, mock_write, mock_img, mock_send):
        mock_cal.return_value = _mock_calendar("buddha_day")
        result = run("morning", dry_run=True)
        assert result["status"] == "dry_run"
        assert result["notification_type"] == "buddha_day"
        mock_write.assert_called_once()
        mock_send.assert_called_once()

    @patch("src.orchestrator.calendar_checker.check")
    def test_buddha_day_evening_skipped(self, mock_cal):
        mock_cal.return_value = _mock_calendar("buddha_day")
        result = run("evening", dry_run=True)
        assert result["status"] == "skipped"
        assert result["reason"] == "mode_mismatch"

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"})
    @patch("src.orchestrator.line_sender.send", return_value={"status": "dry_run", "log_path": "/tmp/test.json"})
    @patch("src.orchestrator.image_picker.pick", return_value="/tmp/test.png")
    @patch("src.orchestrator.message_writer.write", return_value="พรุ่งนี้วันพระค่ะ\nสีแดง\nสาธุค่ะ")
    @patch("src.orchestrator.calendar_checker.check")
    def test_buddha_eve_evening_sent(self, mock_cal, mock_write, mock_img, mock_send):
        mock_cal.return_value = _mock_calendar("buddha_eve", weekday="sunday", color="แดง", date_iso="2025-01-05")
        result = run("evening", dry_run=True)
        assert result["status"] == "dry_run"
        assert result["notification_type"] == "buddha_eve"

    @patch("src.orchestrator.calendar_checker.check")
    def test_no_notification_skipped(self, mock_cal):
        mock_cal.return_value = _mock_calendar(None, date_iso="2025-01-08")
        result = run("morning", dry_run=True)
        assert result["status"] == "skipped"
        assert result["reason"] == "no_notification_today"

"""Tests for calendar_checker module."""

import pytest
from datetime import date

from src.calendar_checker import check, OutOfRangeError


class TestNotificationType:

    def test_buddha_day(self, buddha_day):
        result = check(buddha_day)
        assert result["notification_type"] == "buddha_day"
        assert result["today"]["is_buddha_day"] is True

    def test_buddha_eve(self, kone_day):
        result = check(kone_day)
        assert result["notification_type"] == "buddha_eve"
        assert result["tomorrow"]["is_buddha_day"] is True

    def test_kone_eve(self, kone_eve):
        result = check(kone_eve)
        assert result["notification_type"] == "kone_eve"

    def test_normal_day(self, normal_day):
        result = check(normal_day)
        assert result["notification_type"] is None

    def test_consecutive_buddha_days_july_10(self):
        result = check(date(2025, 7, 10))
        assert result["notification_type"] == "buddha_day"
        assert result["today"]["is_buddha_day"] is True
        assert result["tomorrow"]["is_buddha_day"] is True

    def test_consecutive_buddha_days_july_11(self):
        result = check(date(2025, 7, 11))
        assert result["notification_type"] == "buddha_day"

    def test_eve_of_consecutive_buddha_days(self):
        result = check(date(2025, 7, 9))
        assert result["notification_type"] == "buddha_eve"
        assert result["tomorrow"]["is_buddha_day"] is True


class TestWeekdayColor:

    def test_monday_yellow(self):
        result = check(date(2025, 1, 6))
        assert result["weekday"] == "monday"
        assert result["weekday_color"] == "เหลือง"

    def test_sunday_red(self):
        result = check(date(2025, 1, 5))
        assert result["weekday"] == "sunday"
        assert result["weekday_color"] == "แดง"


class TestOutOfRange:

    def test_before_data_range(self):
        with pytest.raises(OutOfRangeError):
            check(date(2024, 12, 31))

    def test_after_data_range(self):
        with pytest.raises(OutOfRangeError):
            check(date(2027, 1, 1))

    def test_last_day_of_data(self):
        result = check(date(2026, 12, 24))
        assert result["date"] == "2026-12-24"


class TestSchema:

    def test_return_schema_complete(self, buddha_day):
        result = check(buddha_day)
        assert "date" in result
        assert "weekday" in result
        assert "weekday_color" in result
        assert "today" in result
        assert "tomorrow" in result
        assert "notification_type" in result
        assert "is_buddha_day" in result["today"]
        assert "is_kone_day" in result["today"]
        assert "lunar_date" in result["today"]
        assert "is_buddha_day" in result["tomorrow"]
        assert "is_kone_day" in result["tomorrow"]

    def test_default_target_date(self):
        result = check()
        assert result["date"] is not None
        assert isinstance(result["notification_type"], (str, type(None)))

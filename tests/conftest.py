"""Shared fixtures for buddha-noti tests."""

import pytest
from datetime import date


@pytest.fixture
def buddha_day():
    """วันพระ: 2025-01-06 (จันทร์)"""
    return date(2025, 1, 6)


@pytest.fixture
def kone_day():
    """วันโกน (1 วันก่อนวันพระ): 2025-01-05 (อาทิตย์)"""
    return date(2025, 1, 5)


@pytest.fixture
def kone_eve():
    """2 วันก่อนวันพระ: 2025-01-04 (เสาร์)"""
    return date(2025, 1, 4)


@pytest.fixture
def normal_day():
    """วันธรรมดา: ไม่เข้าเงื่อนไขใดเลย"""
    return date(2025, 1, 8)

"""Calendar Checker: ตรวจสอบวันพระ/วันโกนจากข้อมูล JSON"""

import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

BANGKOK = ZoneInfo("Asia/Bangkok")
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "buddha_days.json"

WEEKDAY_NAMES = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday",
}

WEEKDAY_COLORS = {
    0: "เหลือง",
    1: "ชมพู",
    2: "เขียว",
    3: "ส้ม",
    4: "ฟ้า",
    5: "ม่วง",
    6: "แดง",
}


class OutOfRangeError(Exception):
    """วันที่อยู่นอกช่วงข้อมูลใน buddha_days.json"""


_buddha_days: set[date] | None = None
_range_start: date | None = None
_range_end: date | None = None


def _load_buddha_days() -> set[date]:
    global _buddha_days, _range_start, _range_end
    if _buddha_days is not None:
        return _buddha_days

    raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    all_dates: list[date] = []
    years: list[int] = []
    for key, values in raw.items():
        if not isinstance(values, list) or not key.isdigit():
            continue
        years.append(int(key))
        for s in values:
            all_dates.append(date.fromisoformat(s))

    _buddha_days = set(all_dates)
    _range_start = date(min(years), 1, 1)
    _range_end = date(max(years), 12, 31)
    return _buddha_days


def check(target_date: date | None = None) -> dict:
    """ตรวจสอบสถานะวันพระ/วันโกนของ target_date

    Args:
        target_date: วันที่ต้องการเช็ค (default: วันนี้ตาม Asia/Bangkok)

    Returns:
        dict ตาม schema ที่กำหนด

    Raises:
        OutOfRangeError: ถ้าวันที่อยู่นอกช่วงข้อมูล
    """
    buddha_set = _load_buddha_days()

    if target_date is None:
        override = os.environ.get("DATE_OVERRIDE")
        if override:
            target_date = date.fromisoformat(override)
        else:
            target_date = datetime.now(BANGKOK).date()

    if target_date < _range_start or target_date > _range_end:
        raise OutOfRangeError(
            f"วันที่ {target_date} อยู่นอกช่วงข้อมูล ({_range_start} ถึง {_range_end})"
        )

    tomorrow = target_date + timedelta(days=1)
    day_after = target_date + timedelta(days=2)

    today_is_buddha = target_date in buddha_set
    today_is_kone = tomorrow in buddha_set
    tomorrow_is_buddha = tomorrow in buddha_set
    tomorrow_is_kone = day_after in buddha_set

    if today_is_buddha:
        notification_type = "buddha_day"
    elif tomorrow_is_buddha:
        notification_type = "buddha_eve"
    else:
        notification_type = None

    return {
        "date": target_date.isoformat(),
        "weekday": WEEKDAY_NAMES[target_date.weekday()],
        "weekday_color": WEEKDAY_COLORS[target_date.weekday()],
        "today": {
            "is_buddha_day": today_is_buddha,
            "is_kone_day": today_is_kone,
            "lunar_date": None,
        },
        "tomorrow": {
            "is_buddha_day": tomorrow_is_buddha,
            "is_kone_day": tomorrow_is_kone,
        },
        "notification_type": notification_type,
    }

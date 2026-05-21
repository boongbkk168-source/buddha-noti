"""Image Picker: เลือกรูป artwork ตามประเภทแจ้งเตือน (สุ่ม variation A/B)"""

import os
import random
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "images"

# แต่ละ notification_type มี 2 variations — สุ่มเลือกเพื่อความหลากหลาย
VARIATIONS = {
    "buddha_day": ["buddha_day_a.png", "buddha_day_b.png"],
    "buddha_eve": ["buddha_eve_a.png", "buddha_eve_b.png"],
    "kone_eve": ["kone_eve_a.png", "kone_eve_b.png"],
}


def pick(
    weekday_color: str,
    notification_type: str,
    base_dir: Path | None = None,
) -> str:
    """เลือกรูป artwork ตามประเภทแจ้งเตือน (สุ่ม variation A หรือ B)

    Args:
        weekday_color: สีมงคลประจำวัน (คงไว้เพื่อ backward compatibility — ไม่ใช้แล้ว)
        notification_type: "buddha_day" | "buddha_eve" | "kone_eve"
        base_dir: override assets directory (สำหรับ testing)

    Returns:
        absolute path ไปยังไฟล์รูปภาพ

    Note:
        ถ้า env IMAGE_OVERRIDE ถูกตั้งค่า จะคืน path นั้นทันที (สำหรับ testing)
    """
    override = os.environ.get("IMAGE_OVERRIDE")
    if override:
        return str(Path(override).resolve())

    if base_dir is None:
        base_dir = ASSETS_DIR

    choices = VARIATIONS.get(notification_type, VARIATIONS["buddha_day"])
    filename = random.choice(choices)
    return str((base_dir / filename).resolve())

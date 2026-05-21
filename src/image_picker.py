"""Image Picker: เลือกรูป artwork ตามสีมงคลประจำวัน (สุ่ม variation A/B)"""

import os
import random
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "images"

# สีมงคล (ไทย) -> ชื่อไฟล์ (อังกฤษ)
COLOR_KEY = {
    "แดง": "red",
    "เหลือง": "yellow",
    "ชมพู": "pink",
    "เขียว": "green",
    "ส้ม": "orange",
    "ฟ้า": "blue",
    "ม่วง": "purple",
}

VARIATIONS = ["a", "b"]


def pick(
    weekday_color: str,
    notification_type: str,
    base_dir: Path | None = None,
) -> str:
    """เลือกรูป artwork ตามสีมงคลประจำวัน (สุ่ม variation A หรือ B)

    Args:
        weekday_color: สีมงคลประจำวัน (แดง/เหลือง/ชมพู/เขียว/ส้ม/ฟ้า/ม่วง)
        notification_type: ประเภทแจ้งเตือน (คงไว้เพื่อ backward compatibility —
            ไม่ใช้แล้ว เพราะรูปไม่มีข้อความ จึงใช้ได้กับทุกประเภท)
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

    color_en = COLOR_KEY.get(weekday_color, "yellow")
    variation = random.choice(VARIATIONS)
    filename = f"{color_en}_{variation}.png"
    return str((base_dir / filename).resolve())

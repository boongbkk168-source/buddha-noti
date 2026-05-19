"""Image Picker: เลือก/สร้างรูปภาพตามสีมงคล"""

import platform
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "images"

COLOR_MAP = {
    "แดง": (220, 50, 50),
    "เหลือง": (240, 200, 50),
    "ชมพู": (240, 130, 160),
    "เขียว": (60, 180, 75),
    "ส้ม": (240, 150, 30),
    "ฟ้า": (70, 160, 230),
    "ม่วง": (150, 70, 180),
}

COLOR_KEY_MAP = {
    "แดง": "red",
    "เหลือง": "yellow",
    "ชมพู": "pink",
    "เขียว": "green",
    "ส้ม": "orange",
    "ฟ้า": "blue",
    "ม่วง": "purple",
}

TYPE_LABELS_THAI = {
    "buddha_day": "วันพระ",
    "buddha_eve": "วันพระ",
    "kone_eve": "วันโกน",
}

TYPE_LABELS_EN = {
    "buddha_day": "Buddha Day",
    "buddha_eve": "Buddha Day",
    "kone_eve": "Kone Day",
}

TYPE_KEY = {
    "buddha_day": "buddha",
    "buddha_eve": "buddha",
    "kone_eve": "kone",
}

_thai_font_path: str | None = None


def _find_thai_font() -> str | None:
    global _thai_font_path
    if _thai_font_path is not None:
        return _thai_font_path

    candidates = []
    if platform.system() == "Windows":
        candidates = [
            "C:/Windows/Fonts/tahoma.ttf",
            "C:/Windows/Fonts/leelawadee.ttf",
            "C:/Windows/Fonts/cordia.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/thai/Tahoma.ttf",
            "/usr/share/fonts/truetype/tlwg/TlwgTypo.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

    for path in candidates:
        if Path(path).exists():
            _thai_font_path = path
            return _thai_font_path
    return None


def _generate_placeholder(
    color_name: str,
    rgb: tuple[int, int, int],
    notification_type: str,
    output_path: Path,
) -> None:
    img = Image.new("RGB", (1024, 1024), rgb)
    draw = ImageDraw.Draw(img)

    font_path = _find_thai_font()
    if font_path:
        label = TYPE_LABELS_THAI[notification_type]
        font_large = ImageFont.truetype(font_path, 80)
        font_small = ImageFont.truetype(font_path, 40)
    else:
        label = TYPE_LABELS_EN[notification_type]
        font_large = ImageFont.load_default(size=80)
        font_small = ImageFont.load_default(size=40)

    text_color = (255, 255, 255)

    bbox = draw.textbbox((0, 0), label, font=font_large)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((1024 - tw) / 2, (1024 - th) / 2 - 30), label, fill=text_color, font=font_large)

    sub = f"สี{color_name}" if font_path else color_name
    bbox2 = draw.textbbox((0, 0), sub, font=font_small)
    sw = bbox2[2] - bbox2[0]
    draw.text(((1024 - sw) / 2, (1024 + th) / 2 + 20), sub, fill=text_color, font=font_small)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")


def _ensure_placeholders(base_dir: Path) -> None:
    for color_thai, rgb in COLOR_MAP.items():
        color_en = COLOR_KEY_MAP[color_thai]
        for ntype, type_key in TYPE_KEY.items():
            filename = f"{color_en}_{type_key}.png"
            filepath = base_dir / filename
            if not filepath.exists():
                _generate_placeholder(color_thai, rgb, ntype, filepath)


def pick(weekday_color: str, notification_type: str, base_dir: Path | None = None) -> str:
    """เลือกรูปภาพตามสีมงคลและประเภทแจ้งเตือน

    Args:
        weekday_color: สีมงคลประจำวัน
        notification_type: "buddha_day" | "buddha_eve" | "kone_eve"
        base_dir: override assets directory (สำหรับ testing)

    Returns:
        absolute path ไปยังไฟล์รูปภาพ
    """
    if base_dir is None:
        base_dir = ASSETS_DIR

    _ensure_placeholders(base_dir)

    color_en = COLOR_KEY_MAP.get(weekday_color, "red")
    type_key = TYPE_KEY.get(notification_type, "buddha")
    filename = f"{color_en}_{type_key}.png"

    return str((base_dir / filename).resolve())

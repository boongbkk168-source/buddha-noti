"""Preview: เรียก write() จริงผ่าน OpenRouter API เพื่อดูตัวอย่างข้อความ"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.message_writer import write

SAMPLES = [
    ("kone_eve", "saturday", "ม่วง", "2025-01-04"),
    ("kone_eve", "monday", "เหลือง", "2025-02-03"),
    ("kone_eve", "friday", "ฟ้า", "2025-03-07"),
    ("buddha_eve", "sunday", "แดง", "2025-01-05"),
    ("buddha_eve", "tuesday", "ชมพู", "2025-02-04"),
    ("buddha_eve", "wednesday", "เขียว", "2025-03-05"),
    ("buddha_day", "monday", "เหลือง", "2025-01-06"),
    ("buddha_day", "wednesday", "เขียว", "2025-02-05"),
    ("buddha_day", "thursday", "ส้ม", "2025-03-06"),
]


def main():
    model = os.environ.get("LLM_MODEL", "anthropic/claude-sonnet-4.5")
    print(f"Model: {model}")
    print(f"API Key: {'SET' if os.environ.get('OPENROUTER_API_KEY') else 'NOT SET'}")

    for i, (ntype, weekday, color, date_iso) in enumerate(SAMPLES, 1):
        print(f"\n{'='*50}")
        print(f"[{i}/9] type={ntype}  weekday={weekday}  color={color}  date={date_iso}")
        print(f"{'='*50}")
        try:
            text = write(ntype, weekday, color, date_iso)
            print(text)
        except Exception as e:
            print(f"ERROR: {e}")


if __name__ == "__main__":
    main()

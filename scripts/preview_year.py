"""Preview: แสดงวันที่มี notification ทั้งปี 2025"""

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.calendar_checker import check

OUTPUT_FILE = Path(__file__).resolve().parent / "preview_2025.txt"


def main():
    lines = []
    header = f"{'DATE':<12} {'WEEKDAY':<12} {'TYPE':<14} {'COLOR'}"
    lines.append(header)
    lines.append("-" * len(header))

    d = date(2025, 1, 1)
    end = date(2025, 12, 31)
    count = 0

    while d <= end:
        result = check(d)
        if result["notification_type"] is not None:
            line = f"{result['date']:<12} {result['weekday']:<12} {result['notification_type']:<14} {result['weekday_color']}"
            lines.append(line)
            count += 1
        d += timedelta(days=1)

    lines.append(f"\nTotal: {count} notification days in 2025")

    output = "\n".join(lines)
    OUTPUT_FILE.write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()

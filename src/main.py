"""buddha-noti: Bot แจ้งเตือนวันพระไปยัง LINE Group"""

import json
import logging
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

# Ensure UTF-8 output on Linux CI (default may be ASCII)
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Buddha Day LINE Notification Bot")
    parser.add_argument(
        "--mode",
        choices=["morning", "evening"],
        required=True,
        help="morning (05:30 วันพระ) or evening (20:00 ก่อนวันโกน/วันพระ)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        dest="dry_run",
        help="Print message without sending to LINE (default)",
    )
    parser.add_argument(
        "--no-dry-run",
        action="store_false",
        dest="dry_run",
        help="Send message to LINE for real",
    )
    args = parser.parse_args()

    from src.orchestrator import run

    try:
        result = run(mode=args.mode, dry_run=args.dry_run)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)
    except Exception as e:
        logging.getLogger(__name__).error("Fatal: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()

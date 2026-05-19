"""Check required environment variables before running main.py"""

import os
import sys

REQUIRED = [
    "OPENROUTER_API_KEY",
    "LINE_CHANNEL_ACCESS_TOKEN",
    "LINE_GROUP_ID",
]


def main():
    missing = [v for v in REQUIRED if not os.environ.get(v)]
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}", file=sys.stderr)
        print("Set them in .env (local) or GitHub Secrets (CI)", file=sys.stderr)
        sys.exit(1)
    print("All required environment variables are set.")


if __name__ == "__main__":
    main()

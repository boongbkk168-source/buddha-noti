"""LINE Sender: ส่งข้อความไปยัง LINE Group"""

import json
import logging
import os
import random
import string
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

BANGKOK = ZoneInfo("Asia/Bangkok")
LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
PUSH_URL = "https://api.line.me/v2/bot/message/push"
MAX_RETRIES = 2
RETRY_DELAYS = [2, 4]

logger = logging.getLogger(__name__)


class LineSendError(Exception):
    """LINE API ส่งข้อความไม่สำเร็จ"""


def _mask_group_id() -> str:
    gid = os.environ.get("LINE_GROUP_ID", "")
    if not gid:
        return "NOT_SET"
    return "****" + gid[-4:]


def _parse_error_detail(resp: requests.Response) -> str:
    try:
        return resp.json().get("message", resp.text)
    except (ValueError, AttributeError):
        return resp.text or str(resp.status_code)


def _send_push(message: str) -> dict:
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
    group_id = os.environ.get("LINE_GROUP_ID", "")

    if not token:
        raise LineSendError("LINE_CHANNEL_ACCESS_TOKEN not set")
    if not group_id:
        raise LineSendError("LINE_GROUP_ID not set")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    payload = {
        "to": group_id,
        "messages": [{"type": "text", "text": message}],
    }

    masked_gid = _mask_group_id()
    logger.info("Sending push: group=%s, length=%d", masked_gid, len(message))

    last_error = None
    for attempt in range(1 + MAX_RETRIES):
        start = time.monotonic()
        try:
            resp = requests.post(PUSH_URL, headers=headers, json=payload, timeout=10)
            duration_ms = int((time.monotonic() - start) * 1000)
            request_id = resp.headers.get("x-line-request-id", "")

            logger.info(
                "LINE response: status=%d, request_id=%s, duration_ms=%d",
                resp.status_code, request_id, duration_ms,
            )

            if resp.status_code == 200:
                return {"status": "sent", "request_id": request_id, "dry_run": False}

            if resp.status_code == 400:
                raise LineSendError(f"Bad request (400): {_parse_error_detail(resp)}")
            if resp.status_code == 401:
                raise LineSendError(f"Invalid token (401): {_parse_error_detail(resp)}")
            if resp.status_code == 403:
                raise LineSendError(f"Bot not in group or permission denied (403): {_parse_error_detail(resp)}")

            last_error = LineSendError(f"HTTP {resp.status_code}: {_parse_error_detail(resp)}")

        except (requests.Timeout, requests.ConnectionError) as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.warning("Request failed: %s, duration_ms=%d", type(exc).__name__, duration_ms)
            last_error = LineSendError(f"{type(exc).__name__}: {exc}")

        if attempt < MAX_RETRIES:
            delay = RETRY_DELAYS[attempt]
            logger.warning("Retry %d/%d in %ds", attempt + 1, MAX_RETRIES, delay)
            time.sleep(delay)

    raise last_error


def send(
    message: str,
    image_path: str | None = None,
    dry_run: bool = True,
) -> dict:
    if not dry_run:
        # TODO Phase 3.2: แนบรูปภาพ (image_path)
        return _send_push(message)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now(BANGKOK)
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    filename = f"dry_run_{now.strftime('%Y%m%d_%H%M%S')}_{rand}.json"

    log_data = {
        "timestamp_iso": now.isoformat(),
        "message": message,
        "image_path": image_path,
        "target_group_id_masked": _mask_group_id(),
        "dry_run": True,
    }

    log_path = LOGS_DIR / filename
    log_path.write_text(
        json.dumps(log_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {"status": "dry_run", "log_path": str(log_path)}

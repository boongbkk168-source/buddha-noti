"""Orchestrator: ควบคุมการทำงานทั้งหมด"""

import logging
import time

from src import calendar_checker, image_picker, line_sender, message_writer

logger = logging.getLogger(__name__)

MODE_ALLOWED_TYPES = {
    "morning": ["buddha_day"],
    "evening": ["buddha_eve", "kone_eve"],
}


def run(mode: str, dry_run: bool = True) -> dict:
    """Entry point สำหรับ orchestrator

    Args:
        mode: "morning" หรือ "evening"
        dry_run: ถ้า True จะไม่ส่ง LINE จริง

    Returns:
        dict สรุปผลการทำงาน
    """
    start = time.monotonic()

    cal = calendar_checker.check()
    notification_type = cal["notification_type"]

    if notification_type is None:
        return {
            "status": "skipped",
            "reason": "no_notification_today",
            "mode": mode,
            "date": cal["date"],
            "total_duration_ms": int((time.monotonic() - start) * 1000),
        }

    allowed = MODE_ALLOWED_TYPES.get(mode, [])
    if notification_type not in allowed:
        return {
            "status": "skipped",
            "reason": "mode_mismatch",
            "mode": mode,
            "notification_type": notification_type,
            "date": cal["date"],
            "total_duration_ms": int((time.monotonic() - start) * 1000),
        }

    logger.info("Generating message: type=%s color=%s", notification_type, cal["weekday_color"])
    message = message_writer.write(
        notification_type=notification_type,
        weekday=cal["weekday"],
        weekday_color=cal["weekday_color"],
        date_iso=cal["date"],
    )

    logger.info("Picking image: color=%s type=%s", cal["weekday_color"], notification_type)
    image_path = image_picker.pick(
        weekday_color=cal["weekday_color"],
        notification_type=notification_type,
    )

    logger.info("Sending: dry_run=%s", dry_run)
    line_result = line_sender.send(
        message=message,
        image_path=image_path,
        dry_run=dry_run,
    )

    total_ms = int((time.monotonic() - start) * 1000)
    logger.info("Done in %dms", total_ms)

    return {
        "status": "sent" if not dry_run else "dry_run",
        "mode": mode,
        "notification_type": notification_type,
        "date": cal["date"],
        "weekday_color": cal["weekday_color"],
        "message_preview": message[:80] + ("..." if len(message) > 80 else ""),
        "image_path": image_path,
        "line_result": line_result,
        "total_duration_ms": total_ms,
    }

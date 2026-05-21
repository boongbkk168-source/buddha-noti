"""Message Writer: generate ข้อความแจ้งเตือนผ่าน OpenRouter (OpenAI-compatible)"""

import logging
import os
import re
import time

import openai

logger = logging.getLogger(__name__)

PREFIXES = {
    "kone_eve": "พรุ่งนี้วันโกนค่ะ",
    "buddha_eve": "พรุ่งนี้วันพระค่ะ",
    "buddha_day": "วันนี้วันพระค่ะ",
}

TYPE_DESCRIPTIONS = {
    "kone_eve": "ก่อนวันโกน (2 วันก่อนวันพระ)",
    "buddha_eve": "ก่อนวันพระ (วันโกน)",
    "buddha_day": "วันพระ",
}

WEEKDAY_THAI = {
    "monday": "จันทร์",
    "tuesday": "อังคาร",
    "wednesday": "พุธ",
    "thursday": "พฤหัสบดี",
    "friday": "ศุกร์",
    "saturday": "เสาร์",
    "sunday": "อาทิตย์",
}

FALLBACK_TEMPLATES = {
    "kone_eve": "พรุ่งนี้วันโกนค่ะ 🌸\nสีมงคลวันนี้คือสี{color} ✨\nเตรียมตัวทำบุญกันนะคะ 🙏\nขอให้มีความสุขค่ะ",
    "buddha_eve": "พรุ่งนี้วันพระค่ะ 🪷\nสีมงคลวันนี้คือสี{color} ✨\nเตรียมใจใส่บุญกันค่ะ 🙏\nสาธุค่ะ",
    "buddha_day": "วันนี้วันพระค่ะ 🙏\nสีมงคลวันนี้คือสี{color} ☀️\nทำบุญ ตักบาตร รักษาศีลกันนะคะ 🪷\nขอบุญรักษาค่ะ",
}

# emoji น่ารักแนะนำตาม notification_type
EMOJI_HINTS = {
    "kone_eve": "🌸 🪷 ✨ 💐",
    "buddha_eve": "🪷 🕯️ ✨ 🌙",
    "buddha_day": "🙏 🪷 ☀️ 🏵️",
}

SYSTEM_PROMPT = (
    "คุณเป็นบอทแจ้งเตือนวันพระสำหรับ LINE group "
    "เขียนข้อความสั้นเป็นภาษาไทย สุภาพ ใช้คำลงท้ายผู้หญิง (\"ค่ะ\") "
    "ข้อความต้อง 3-5 บรรทัด ไม่เกิน 500 ตัวอักษร "
    "ใส่อิโมจิน่ารักที่เหมาะกับธีมพุทธศาสนา 3-4 ตัว "
    "(เช่น 🙏 🪷 ✨ 🌸 ☀️ 🕯️ 🌙 💐 🏵️ 🎋) กระจายในข้อความ ไม่กองรวมกัน ห้ามใช้ markdown "
    "ลงท้ายบรรทัดสุดท้ายด้วย \"ค่ะ\" เสมอ"
)

MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]
MAX_REGEN = 2


class ConfigError(Exception):
    """ไม่พบ configuration ที่จำเป็น"""


def _get_client() -> openai.OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ConfigError("ไม่พบ OPENROUTER_API_KEY ใน environment variables")
    return openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "https://github.com/buddha-noti",
            "X-Title": "buddha-noti",
        },
    )


def _validate(text: str, notification_type: str, weekday_color: str) -> bool:
    prefix = PREFIXES.get(notification_type, "")
    if not text.startswith(prefix):
        return False

    if weekday_color not in text:
        return False

    stripped = re.sub(r"[\s\U00010000-\U0010ffff☀-➿⌀-⏿️]+$", "", text)
    if not stripped.endswith("ค่ะ"):
        return False

    lines = [line for line in text.strip().splitlines() if line.strip()]
    if not (3 <= len(lines) <= 5):
        return False

    if len(text) > 500:
        return False

    return True


def _build_user_prompt(
    notification_type: str,
    weekday: str,
    weekday_color: str,
    date_iso: str,
) -> str:
    prefix = PREFIXES[notification_type]
    type_desc = TYPE_DESCRIPTIONS[notification_type]
    weekday_th = WEEKDAY_THAI.get(weekday, weekday)
    emoji_hint = EMOJI_HINTS[notification_type]

    return (
        f"เขียนข้อความแจ้งเตือน{type_desc}\n"
        f"วันที่: {date_iso}\n"
        f"วัน: {weekday_th}\n"
        f"สีมงคล: {weekday_color}\n\n"
        f"กฎ:\n"
        f'- ขึ้นต้นด้วย "{prefix}"\n'
        f'- ระบุสีมงคล "{weekday_color}" ในข้อความ\n'
        f"- เนื้อหาเกี่ยวกับธรรมะ/อวยพร\n"
        f'- ลงท้ายด้วย "ค่ะ"\n'
        f"- 3-5 บรรทัด ไม่เกิน 500 ตัวอักษร\n"
        f"- ใส่อิโมจิน่ารัก 3-4 ตัว (แนะนำ: {emoji_hint}) กระจายในข้อความ ไม่กองรวมกัน\n"
        f"- ห้ามใช้ markdown"
    )


def _call_api(client: openai.OpenAI, model: str, user_prompt: str) -> str:
    start = time.monotonic()
    response = client.chat.completions.create(
        model=model,
        max_tokens=500,
        temperature=0.8,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    latency_ms = int((time.monotonic() - start) * 1000)
    usage = response.usage
    logger.info(
        "LLM API: model=%s input_tokens=%d output_tokens=%d latency=%dms",
        model,
        usage.prompt_tokens if usage else 0,
        usage.completion_tokens if usage else 0,
        latency_ms,
    )
    return response.choices[0].message.content.strip()


def _fallback(notification_type: str, weekday_color: str) -> str:
    template = FALLBACK_TEMPLATES[notification_type]
    return template.format(color=weekday_color)


def write(
    notification_type: str,
    weekday: str,
    weekday_color: str,
    date_iso: str,
) -> str:
    """Generate ข้อความแจ้งเตือนวันพระ

    Args:
        notification_type: "kone_eve" | "buddha_eve" | "buddha_day"
        weekday: "monday" ... "sunday"
        weekday_color: สีมงคลประจำวัน
        date_iso: "2025-01-06"

    Returns:
        ข้อความภาษาไทย 3-5 บรรทัด

    Raises:
        ConfigError: ถ้าไม่พบ OPENROUTER_API_KEY
    """
    client = _get_client()
    model = os.environ.get("LLM_MODEL", "anthropic/claude-sonnet-4.5")
    user_prompt = _build_user_prompt(notification_type, weekday, weekday_color, date_iso)

    total_attempts = MAX_REGEN + 1
    for regen in range(total_attempts):
        for attempt in range(MAX_RETRIES):
            try:
                text = _call_api(client, model, user_prompt)
                if _validate(text, notification_type, weekday_color):
                    return text
                logger.warning("Validation failed (regen %d), regenerating", regen + 1)
                break
            except (
                openai.RateLimitError,
                openai.InternalServerError,
                openai.APITimeoutError,
                openai.APIConnectionError,
            ):
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAYS[attempt])
                    continue
                logger.warning("API failed after %d retries, using fallback", MAX_RETRIES)
                return _fallback(notification_type, weekday_color)
            except (openai.AuthenticationError, openai.BadRequestError):
                logger.warning("Non-retryable API error, using fallback")
                return _fallback(notification_type, weekday_color)
            except openai.APIError:
                logger.warning("Unexpected API error, using fallback")
                return _fallback(notification_type, weekday_color)

    logger.warning("All regeneration attempts failed validation, using fallback")
    return _fallback(notification_type, weekday_color)

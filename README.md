# buddha-noti

Bot แจ้งเตือนวันพระไปยัง LINE Group อัตโนมัติ ทำงานผ่าน GitHub Actions

## Features
- แจ้งเตือน 2 รอบต่อวันพระ: ก่อนวันพระ, วันพระ
- ข้อความธรรมะ generate ใหม่ทุกครั้งผ่าน OpenRouter API (Claude)
- สีมงคลประจำวัน
- รองรับ dry-run สำหรับ testing

## Setup

### 1. LINE Messaging API Channel

1. ไปที่ [LINE Developers Console](https://developers.line.biz/console/)
2. สร้าง Provider > สร้าง Channel ประเภท **Messaging API**
3. Issue **Channel Access Token** (long-lived)
4. ปิด Auto-reply messages
5. เพิ่ม Bot เข้า LINE Group ที่ต้องการ
6. หา **Group ID** จาก webhook event

### 2. OpenRouter API Key

1. ไปที่ [OpenRouter](https://openrouter.ai/keys)
2. สร้าง API Key

### 3. ติดตั้ง Local

```bash
git clone <repo-url>
cd buddha-noti
pip install -r requirements.txt
cp .env.example .env
# แก้ไขค่าใน .env ให้ครบ
```

### 4. ทดสอบ

```bash
# Unit tests
pytest tests/ -v

# Dry-run (ไม่ส่ง LINE จริง)
python src/main.py --mode morning --dry-run
python src/main.py --mode evening --dry-run

# ส่งจริง
python src/main.py --mode morning --no-dry-run
```

## Deployment (GitHub Actions)

### ตั้ง Secrets

ไปที่ repo > Settings > Secrets and variables > Actions > New repository secret:

| Secret | ค่า |
|--------|-----|
| `OPENROUTER_API_KEY` | API Key จาก OpenRouter |
| `LINE_CHANNEL_ACCESS_TOKEN` | Channel Access Token จาก LINE Developers |
| `LINE_GROUP_ID` | Group ID ของ LINE Group |
| `LLM_MODEL` | (optional) default: `anthropic/claude-sonnet-4.5` |

### Cron Schedule

Workflow ทำงานอัตโนมัติ 2 รอบ/วัน:

| เวลา (ICT) | UTC | Mode | แจ้งเตือน |
|------------|-----|------|----------|
| 05:30 | 22:30 (วันก่อน) | morning | วันพระ |
| 20:00 | 13:00 | evening | ก่อนวันพระ |

### Manual Trigger

1. ไปที่ **Actions** tab
2. เลือก **Buddha Noti**
3. คลิก **Run workflow**
4. เลือก mode, dry_run, date_override (optional)

### ดู Logs

หลังรัน workflow เสร็จ > คลิก run > Artifacts > **logs-{run_id}** > Download

## Architecture

```
GitHub Actions (cron/manual)
    > main.py --mode morning|evening [--dry-run]
        > orchestrator
            > calendar-checker
            > message-writer (OpenRouter API)
            > image-picker
            > line-sender (LINE Messaging API)
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | OpenRouter API key |
| `LINE_CHANNEL_ACCESS_TOKEN` | Yes | LINE channel access token |
| `LINE_GROUP_ID` | Yes | LINE group ID to send messages to |
| `LLM_MODEL` | No | LLM model (default: `anthropic/claude-sonnet-4.5`) |
| `DATE_OVERRIDE` | No | Override date for testing (YYYY-MM-DD) |

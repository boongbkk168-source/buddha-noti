# buddha-noti

Bot แจ้งเตือนวันพระไปยัง LINE Group อัตโนมัติ

## Tech Stack
- Python 3.11+
- LINE Messaging API (push message to group)
- GitHub Actions cron (scheduler)
- OpenRouter via `openai` SDK (generate ข้อความ, OpenAI-compatible gateway)
- Timezone: Asia/Bangkok เสมอ (ใช้ `zoneinfo`)

## วิธี Run

```bash
# ติดตั้ง dependencies
pip install -r requirements.txt

# copy .env
cp .env.example .env
# แก้ไขค่าใน .env

# รันแบบ dry-run (ไม่ส่ง LINE จริง)
python src/main.py --mode morning --dry-run
python src/main.py --mode evening --dry-run

# รันจริง
python src/main.py --mode morning
```

## วิธี Test

```bash
pytest tests/ -v
```

## โครงสร้าง Sub-Agents

| Agent | หน้าที่ |
|-------|---------|
| orchestrator | รับ mode, ตัดสินใจส่งหรือไม่, เรียก agents ตามลำดับ |
| calendar-checker | เช็ควันพระ/วันโกน คืนข้อมูลวัน |
| message-writer | generate ข้อความธรรมะผ่าน OpenRouter API |
| image-picker | เลือกรูปตามสีมงคล |
| line-sender | push message + image ไป LINE group |

## ตารางแจ้งเตือน

| ประเภท | วันที่ส่ง | เวลา | ขึ้นต้น |
|--------|----------|-------|--------|
| ก่อนวันพระ | วันโกน | 20:00 | "พรุ่งนี้วันพระค่ะ..." |
| วันพระ | วันพระ | 05:30 | "วันนี้วันพระค่ะ..." |

## สีมงคลประจำวัน
อา=แดง, จ=เหลือง, อ=ชมพู, พ=เขียว, พฤ=ส้ม, ศ=ฟ้า, ส=ม่วง

## Conventions
- ข้อความลงท้ายด้วย "ค่ะ" เสมอ
- ข้อความยาว 3-5 บรรทัด generate ใหม่ทุกครั้ง
- ใช้ `zoneinfo` ไม่ใช้ `pytz`
- วันพระ hardcode ใน `data/buddha_days.json`
- Secrets อยู่ใน `.env` (local) และ GitHub Secrets (CI)
- Env vars: `OPENROUTER_API_KEY`, `LLM_MODEL`, `LINE_CHANNEL_ACCESS_TOKEN`, `LINE_GROUP_ID`
- `DATE_OVERRIDE=YYYY-MM-DD` เพื่อ override วันที่ (testing)

# LIMITLESS OS — Self-Healing AI Agent

An autonomous agent that monitors your n8n automation system, diagnoses failures using Claude AI, auto-fixes transient errors, and reports to Telegram every morning.

---

## Architecture

```
agent.py          Main loop — polls every 5 min, schedules daily report
healer.py         Classifies errors (Claude API) and executes fixes
reporter.py       Telegram alerts + JSONL audit log
sheets.py         Google Sheets integration (DLQ + Follow_Up_Tracker)
config.py         All settings loaded from .env
```

### Data Flow

```
Every 5 minutes:
  ┌─ n8n API ──→ failed executions ──→ Healer ──→ Claude classify ──→ retry / alert
  ├─ Google Sheets DLQ ──→ open errors ──→ Healer ──→ Claude classify ──→ alert
  └─ Follow_Up_Tracker ──→ stuck drafts ──→ Healer ──→ webhook reset

Every morning 07:45:
  Reporter ──→ Telegram summary ("✅ Auto-fixed: X  ⚠️ Needs attention: Y")

All decisions:
  Reporter ──→ decisions.jsonl (append-only audit trail)
```

---

## Requirements

- Python 3.11 or higher
- A running n8n instance with API access enabled
- (Optional) Google service account with Sheets read access
- (Optional) Telegram bot token
- (Optional) Anthropic API key

The agent runs without Google Sheets or Telegram if those credentials are omitted — it will log warnings and skip those integrations.

---

## Setup

### 1. Clone / copy the files

```bash
cd limitless_os/
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate       # Linux / macOS
# .venv\Scripts\activate        # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
nano .env    # fill in your values
```

Minimum required variables:

| Variable | Description |
|---|---|
| `N8N_BASE_URL` | Your n8n instance URL, e.g. `https://n8n.example.com` |
| `N8N_API_KEY` | n8n API key (Settings → API → Create API Key) |

All other variables are optional but enable additional features.

### 5. (Optional) Google Sheets setup

1. Create a Google Cloud project and enable the Sheets API
2. Create a service account and download the JSON credentials file
3. Share your spreadsheet with the service account's email address (read-only is fine)
4. Set `GOOGLE_SERVICE_ACCOUNT_JSON` to the path of the credentials file
5. Set `SPREADSHEET_ID` to your spreadsheet's ID

**Expected sheet columns:**

*DLQ tab:*
| contact_id | error_message | workflow_name | created_at | status |
|---|---|---|---|---|

*Follow_Up_Tracker tab:*
| contact_id | status | draft_created_date |
|---|---|---|

### 6. (Optional) Telegram setup

1. Message [@BotFather](https://t.me/botfather) → `/newbot`
2. Copy the token to `TELEGRAM_BOT_TOKEN`
3. Add the bot to your group or start a chat with it
4. Visit `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your `chat_id`
5. Set `TELEGRAM_CHAT_ID`

### 7. Run the agent

```bash
python agent.py
```

---

## Running as a systemd Service (Recommended for Linux)

```ini
# /etc/systemd/system/limitless-os.service

[Unit]
Description=LIMITLESS OS Self-Healing Agent
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/limitless_os
ExecStart=/path/to/limitless_os/.venv/bin/python agent.py
Restart=on-failure
RestartSec=30
EnvironmentFile=/path/to/limitless_os/.env
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable limitless-os
sudo systemctl start limitless-os
sudo journalctl -u limitless-os -f    # tail logs
```

---

## Running with Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "agent.py"]
```

```bash
docker build -t limitless-os .
docker run -d \
  --name limitless-os \
  --restart unless-stopped \
  --env-file .env \
  -v /path/to/service-account.json:/app/service-account.json:ro \
  limitless-os
```

---

## Audit Log

Every decision is appended to `decisions.jsonl`:

```jsonl
{"ts":"2026-03-09T07:45:00Z","source":"n8n","item_id":"12345","error_class":"transient","action":"retried","success":true,"explanation":"Timeout connecting to external API","session_auto_fixed":3,"session_needs_attention":1}
{"ts":"2026-03-09T07:46:00Z","source":"dlq","item_id":"contact_abc","error_class":"data_issue","action":"alerted","success":true,"explanation":"Missing required field: email","session_auto_fixed":3,"session_needs_attention":2}
```

Useful queries:
```bash
# All failed retries today
grep '"action":"retried","success":false' decisions.jsonl

# Code bugs requiring attention
grep '"error_class":"code_bug"' decisions.jsonl

# Count by action
cat decisions.jsonl | python3 -c "
import sys, json, collections
c = collections.Counter(json.loads(l)['action'] for l in sys.stdin)
print(dict(c))
"
```

---

## Error Classification

Claude classifies each error into one of five categories:

| Class | Meaning | Action |
|---|---|---|
| `transient` | Network timeout, temporary outage | Auto-retry via n8n API |
| `data_issue` | Bad input, missing required fields | Alert to Telegram |
| `code_bug` | Logic error in workflow | Alert to Telegram |
| `rate_limit` | 429 / quota exceeded | Back off 10 min, then retry |
| `unknown` | Cannot determine | Alert to Telegram |

If the Claude API is unavailable, a heuristic classifier takes over (keyword matching on the error message).

---

## Monitoring the Agent

The agent logs structured JSON to stdout:

```json
{"ts":"2026-03-09T07:45:00Z","level":"INFO","module":"agent","msg":"Poll cycle complete in 2.3s — session: auto_fixed=2 needs_attention=1"}
```

Check agent health:
```bash
# Last 50 lines
journalctl -u limitless-os -n 50

# Only errors
journalctl -u limitless-os -p err

# Since last boot
journalctl -u limitless-os -b
```

---

## Troubleshooting

**Agent won't start:**
- Check that `N8N_BASE_URL` and `N8N_API_KEY` are set in `.env`
- Verify your n8n instance is reachable: `curl https://your-n8n.example.com/healthz`

**No Telegram messages:**
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are correct
- Test with: `curl "https://api.telegram.org/bot<TOKEN>/getMe"`
- Make sure the bot has been added to the chat and has permission to send messages

**Google Sheets returns empty:**
- Verify the service account email has been granted access to the spreadsheet
- Check tab names match exactly (case-sensitive) — `DLQ_TAB_NAME` and `TRACKER_TAB_NAME`
- Confirm column names in the sheet match expected names (see Setup → Google Sheets)

**Claude not classifying errors:**
- Verify `ANTHROPIC_API_KEY` is valid
- The agent falls back to heuristic classification — check logs for `"Claude API error"`

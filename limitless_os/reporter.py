"""
reporter.py — LIMITLESS OS Telegram Reporting & JSONL Audit Log
Tracks session stats, appends structured decisions log, sends Telegram summaries.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx

from healer import HealResult, ErrorClass

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"


# ── Session stats ─────────────────────────────────────────────────────────────

@dataclass
class SessionStats:
    auto_fixed: int = 0
    needs_attention: int = 0
    total_processed: int = 0
    started_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))

    def reset(self) -> None:
        self.auto_fixed = 0
        self.needs_attention = 0
        self.total_processed = 0
        self.started_at = datetime.now(tz=timezone.utc)


# ── Reporter ──────────────────────────────────────────────────────────────────

class Reporter:
    """
    Two responsibilities:
      1. Append every HealResult to decisions.jsonl (audit trail)
      2. Send Telegram messages (daily summary + immediate alerts)
    """

    def __init__(self, config, http_client: httpx.AsyncClient) -> None:
        self._cfg = config
        self._http = http_client
        self._stats = SessionStats()
        self._log_path = Path(config.decisions_log_path)
        # Ensure log file parent directory exists
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Public API ────────────────────────────────────────────────────────────

    def record(self, result: HealResult) -> None:
        """Update session stats and append result to decisions.jsonl."""
        self._stats.total_processed += 1

        auto_fixed_actions = {"retried", "webhook_reset"}
        if result.success and result.action_taken in auto_fixed_actions:
            self._stats.auto_fixed += 1
        elif result.error_class in (
            ErrorClass.DATA_ISSUE,
            ErrorClass.CODE_BUG,
            ErrorClass.UNKNOWN,
        ):
            self._stats.needs_attention += 1

        self._append_jsonl(result)

    async def send_daily_summary(self) -> None:
        """Format and send the morning summary to Telegram, then reset stats."""
        now = datetime.now(tz=timezone.utc)
        text = (
            f"🤖 Agent Report\n"
            f"✅ Auto-fixed: {self._stats.auto_fixed}\n"
            f"⚠️ Needs attention: {self._stats.needs_attention}\n"
            f"📊 Total processed: {self._stats.total_processed}\n"
            f"📅 {now.strftime('%Y-%m-%d %H:%M')} UTC"
        )
        logger.info(
            "Daily summary — auto_fixed=%d needs_attention=%d",
            self._stats.auto_fixed,
            self._stats.needs_attention,
        )
        await self._send_telegram(text)
        self._stats.reset()

    async def send_alert(self, message: str, error_class: Optional[ErrorClass] = None) -> None:
        """Send an immediate alert for issues that need human attention."""
        prefix = {
            ErrorClass.CODE_BUG:    "🐛 Code Bug Detected",
            ErrorClass.DATA_ISSUE:  "📋 Data Issue Detected",
            ErrorClass.UNKNOWN:     "❓ Unknown Error",
        }.get(error_class, "⚠️ Alert")  # type: ignore[arg-type]

        text = f"*{prefix}*\n{message}"
        await self._send_telegram(text, parse_mode="Markdown")

    async def send_shutdown_notice(self) -> None:
        """Notify operator that the agent is stopping."""
        await self._send_telegram("🛑 LIMITLESS OS Agent is shutting down.")

    async def send_startup_notice(self) -> None:
        """Notify operator that the agent has started."""
        await self._send_telegram(
            f"🚀 LIMITLESS OS Agent started\n"
            f"Polling every {self._cfg.n8n_poll_interval_minutes} min\n"
            f"Daily report at {self._cfg.report_time}"
        )

    @property
    def stats(self) -> SessionStats:
        return self._stats

    # ── Telegram ──────────────────────────────────────────────────────────────

    async def _send_telegram(
        self,
        text: str,
        parse_mode: Optional[str] = None,
    ) -> None:
        """POST a message to Telegram. Logs errors but never raises."""
        if not self._cfg.telegram_bot_token or not self._cfg.telegram_chat_id:
            logger.warning("Telegram not configured — message suppressed: %s", text[:80])
            return

        url = f"{TELEGRAM_API}/bot{self._cfg.telegram_bot_token}/sendMessage"
        payload: dict = {
            "chat_id": self._cfg.telegram_chat_id,
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        try:
            resp = await self._http.post(
                url,
                json=payload,
                timeout=httpx.Timeout(10.0),
            )
            if resp.status_code != 200:
                logger.warning(
                    "Telegram returned %d: %s", resp.status_code, resp.text[:200]
                )
            else:
                logger.debug("Telegram message sent (len=%d)", len(text))
        except Exception as exc:
            # Reporting failures must never crash the agent
            logger.error("Failed to send Telegram message: %s", exc)

    # ── JSONL audit log ───────────────────────────────────────────────────────

    def _append_jsonl(self, result: HealResult) -> None:
        """Append one structured JSON line to the decisions log."""
        entry = {
            "ts":                    result.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source":                result.source,
            "item_id":               result.item_id,
            "error_class":           result.error_class.value,
            "action":                result.action_taken,
            "success":               result.success,
            "explanation":           result.explanation,
            "session_auto_fixed":    self._stats.auto_fixed,
            "session_needs_attention": self._stats.needs_attention,
        }
        try:
            with self._log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
                fh.flush()
        except OSError as exc:
            logger.warning("Could not write to %s: %s", self._log_path, exc)

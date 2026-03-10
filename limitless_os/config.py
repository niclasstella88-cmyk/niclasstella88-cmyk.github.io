"""
config.py — LIMITLESS OS Agent Configuration
Loads all settings from environment / .env file.
Raises ValueError at startup if required variables are missing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


@dataclass
class Config:
    # ── n8n ───────────────────────────────────────────────────────────────────
    n8n_base_url: str
    n8n_api_key: str
    n8n_poll_interval_minutes: int = 5
    n8n_stuck_draft_webhook_url: str = ""
    n8n_executions_limit: int = 50

    # ── Google Sheets ─────────────────────────────────────────────────────────
    google_service_account_json: str = ""   # path to credentials JSON file
    spreadsheet_id: str = ""
    dlq_tab_name: str = "DLQ"
    tracker_tab_name: str = "Follow_Up_Tracker"
    stuck_draft_threshold_hours: int = 48

    # ── Anthropic / Claude ────────────────────────────────────────────────────
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"
    claude_max_tokens: int = 256

    # ── Telegram ──────────────────────────────────────────────────────────────
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    report_time: str = "07:45"          # HH:MM in local time

    # ── Logging / audit ──────────────────────────────────────────────────────
    log_level: str = "INFO"
    decisions_log_path: str = "decisions.jsonl"

    # ── HTTP ──────────────────────────────────────────────────────────────────
    http_timeout_seconds: float = 30.0
    http_connect_timeout_seconds: float = 10.0
    http_max_retries: int = 3


def load_config() -> Config:
    """
    Load configuration from .env file and environment variables.

    Required variables (raises ValueError listing ALL missing ones if absent):
      N8N_BASE_URL, N8N_API_KEY

    All other variables have safe defaults.
    """
    load_dotenv()

    def _get(key: str, default: str | None = None) -> str | None:
        return os.environ.get(key, default)

    def _get_int(key: str, default: int) -> int:
        val = os.environ.get(key)
        if val is None:
            return default
        try:
            return int(val)
        except ValueError:
            raise ValueError(f"Config: {key} must be an integer, got {val!r}")

    def _get_float(key: str, default: float) -> float:
        val = os.environ.get(key)
        if val is None:
            return default
        try:
            return float(val)
        except ValueError:
            raise ValueError(f"Config: {key} must be a float, got {val!r}")

    # ── Required vars ────────────────────────────────────────────────────────
    missing: list[str] = []
    n8n_base_url = _get("N8N_BASE_URL") or ""
    n8n_api_key  = _get("N8N_API_KEY") or ""

    if not n8n_base_url:
        missing.append("N8N_BASE_URL")
    if not n8n_api_key:
        missing.append("N8N_API_KEY")

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Copy .env.example to .env and fill in the values."
        )

    return Config(
        # n8n
        n8n_base_url=n8n_base_url.rstrip("/"),
        n8n_api_key=n8n_api_key,
        n8n_poll_interval_minutes=_get_int("N8N_POLL_INTERVAL_MINUTES", 5),
        n8n_stuck_draft_webhook_url=_get("N8N_STUCK_DRAFT_WEBHOOK_URL", "") or "",
        n8n_executions_limit=_get_int("N8N_EXECUTIONS_LIMIT", 50),

        # Google Sheets
        google_service_account_json=_get("GOOGLE_SERVICE_ACCOUNT_JSON", "") or "",
        spreadsheet_id=_get("SPREADSHEET_ID", "") or "",
        dlq_tab_name=_get("DLQ_TAB_NAME", "DLQ") or "DLQ",
        tracker_tab_name=_get("TRACKER_TAB_NAME", "Follow_Up_Tracker") or "Follow_Up_Tracker",
        stuck_draft_threshold_hours=_get_int("STUCK_DRAFT_THRESHOLD_HOURS", 48),

        # Anthropic
        anthropic_api_key=_get("ANTHROPIC_API_KEY", "") or "",
        claude_model=_get("CLAUDE_MODEL", "claude-sonnet-4-6") or "claude-sonnet-4-6",
        claude_max_tokens=_get_int("CLAUDE_MAX_TOKENS", 256),

        # Telegram
        telegram_bot_token=_get("TELEGRAM_BOT_TOKEN", "") or "",
        telegram_chat_id=_get("TELEGRAM_CHAT_ID", "") or "",
        report_time=_get("REPORT_TIME", "07:45") or "07:45",

        # Logging
        log_level=_get("LOG_LEVEL", "INFO") or "INFO",
        decisions_log_path=_get("DECISIONS_LOG_PATH", "decisions.jsonl") or "decisions.jsonl",

        # HTTP
        http_timeout_seconds=_get_float("HTTP_TIMEOUT_SECONDS", 30.0),
        http_connect_timeout_seconds=_get_float("HTTP_CONNECT_TIMEOUT_SECONDS", 10.0),
        http_max_retries=_get_int("HTTP_MAX_RETRIES", 3),
    )

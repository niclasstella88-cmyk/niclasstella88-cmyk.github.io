"""
sheets.py — LIMITLESS OS Google Sheets Integration
Reads DLQ and Follow_Up_Tracker tabs asynchronously.
All blocking gspread I/O is run via asyncio.to_thread().
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# ── Data models ───────────────────────────────────────────────────────────────

@dataclass
class DLQRow:
    row_index: int
    contact_id: str
    error_message: str
    workflow_name: str
    created_at: Optional[datetime]
    status: str
    raw: dict = field(default_factory=dict)


@dataclass
class TrackerRow:
    row_index: int
    contact_id: str
    status: str
    draft_created_date: Optional[datetime]
    raw: dict = field(default_factory=dict)


# ── Client ────────────────────────────────────────────────────────────────────

class SheetsClient:
    """
    Async wrapper around gspread for reading LIMITLESS OS spreadsheet data.

    Requires:
      config.google_service_account_json — path to service account JSON
      config.spreadsheet_id              — Google Sheets spreadsheet ID
    """

    def __init__(self, config) -> None:
        self._config = config
        self._gc = None          # gspread.Client (lazy)
        self._sheet = None       # gspread.Spreadsheet (lazy)

    # ── Public async API ─────────────────────────────────────────────────────

    async def get_dlq_open_errors(self) -> list[DLQRow]:
        """Return all rows in DLQ tab where status != 'resolved'."""
        if not self._sheets_configured():
            logger.warning("Google Sheets not configured — skipping DLQ check")
            return []
        try:
            rows = await asyncio.to_thread(self._fetch_dlq_rows)
            logger.info("DLQ: fetched %d open rows", len(rows))
            return rows
        except Exception as exc:
            logger.error("Failed to read DLQ tab: %s", exc, exc_info=True)
            return []

    async def get_stuck_drafts(self) -> list[TrackerRow]:
        """
        Return rows from Follow_Up_Tracker where:
          status == 'draft_ready'  AND  draft_created_date > STUCK_DRAFT_THRESHOLD_HOURS ago
        """
        if not self._sheets_configured():
            logger.warning("Google Sheets not configured — skipping tracker check")
            return []
        try:
            rows = await asyncio.to_thread(self._fetch_stuck_drafts)
            logger.info("Tracker: found %d stuck drafts", len(rows))
            return rows
        except Exception as exc:
            logger.error("Failed to read Follow_Up_Tracker tab: %s", exc, exc_info=True)
            return []

    # ── Synchronous helpers (run via to_thread) ───────────────────────────────

    def _fetch_dlq_rows(self) -> list[DLQRow]:
        sheet = self._get_worksheet(self._config.dlq_tab_name)
        records = sheet.get_all_records()
        result: list[DLQRow] = []
        for i, rec in enumerate(records, start=2):   # row 1 = header
            status = str(rec.get("status", "")).strip().lower()
            if status == "resolved":
                continue
            result.append(DLQRow(
                row_index=i,
                contact_id=str(rec.get("contact_id", rec.get("id", f"row_{i}"))).strip(),
                error_message=str(rec.get("error_message", rec.get("error", ""))).strip(),
                workflow_name=str(rec.get("workflow_name", rec.get("workflow", ""))).strip(),
                created_at=_parse_datetime(rec.get("created_at", rec.get("timestamp", ""))),
                status=status,
                raw=dict(rec),
            ))
        return result

    def _fetch_stuck_drafts(self) -> list[TrackerRow]:
        sheet = self._get_worksheet(self._config.tracker_tab_name)
        records = sheet.get_all_records()
        threshold = datetime.now(tz=timezone.utc) - timedelta(
            hours=self._config.stuck_draft_threshold_hours
        )
        result: list[TrackerRow] = []
        for i, rec in enumerate(records, start=2):
            status = str(rec.get("status", "")).strip().lower()
            if status != "draft_ready":
                continue
            created_date = _parse_datetime(
                rec.get("draft_created_date", rec.get("created_at", ""))
            )
            if created_date is None:
                logger.warning(
                    "Tracker row %d: cannot parse draft_created_date %r — skipping",
                    i, rec.get("draft_created_date")
                )
                continue
            if created_date > threshold:
                continue   # not stuck yet
            result.append(TrackerRow(
                row_index=i,
                contact_id=str(rec.get("contact_id", rec.get("id", f"row_{i}"))).strip(),
                status=status,
                draft_created_date=created_date,
                raw=dict(rec),
            ))
        return result

    # ── gspread connection ────────────────────────────────────────────────────

    def _get_worksheet(self, tab_name: str):
        """Return a gspread Worksheet, reconnecting if necessary."""
        try:
            import gspread
            from google.oauth2.service_account import Credentials
        except ImportError:
            raise ImportError(
                "gspread and google-auth are required for Google Sheets integration.\n"
                "Run: pip install gspread google-auth"
            )

        if self._gc is None:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets.readonly",
                "https://www.googleapis.com/auth/drive.readonly",
            ]
            creds = Credentials.from_service_account_file(
                self._config.google_service_account_json,
                scopes=scopes,
            )
            self._gc = gspread.authorize(creds)
            logger.debug("gspread: authenticated with service account")

        if self._sheet is None:
            self._sheet = self._gc.open_by_key(self._config.spreadsheet_id)
            logger.debug("gspread: opened spreadsheet %s", self._config.spreadsheet_id)

        try:
            return self._sheet.worksheet(tab_name)
        except Exception:
            # Force reconnect on next call
            self._gc = None
            self._sheet = None
            raise

    def _sheets_configured(self) -> bool:
        return bool(
            self._config.google_service_account_json
            and self._config.spreadsheet_id
        )


# ── Utilities ─────────────────────────────────────────────────────────────────

def _parse_datetime(value: object) -> Optional[datetime]:
    """
    Parse a datetime from various string formats found in Google Sheets.
    Returns a UTC-aware datetime, or None if parsing fails.
    """
    if not value:
        return None
    s = str(value).strip()
    if not s:
        return None

    # Try common formats
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
        "%m/%d/%Y",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            # Assume UTC if no timezone info
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    logger.debug("_parse_datetime: could not parse %r", s)
    return None

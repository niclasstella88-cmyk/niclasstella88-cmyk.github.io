"""
agent.py — LIMITLESS OS Self-Healing Agent (Main Entry Point)

Runs a continuous async loop that:
  - Polls n8n every N minutes for failed executions
  - Checks Google Sheets DLQ for open errors
  - Detects stuck drafts in Follow_Up_Tracker
  - Sends a daily Telegram summary at 07:45
  - Logs every decision to decisions.jsonl
"""

from __future__ import annotations

import asyncio
import json
import logging
import logging.config
import signal
import sys
from datetime import datetime, timezone

import httpx
import schedule

from config import Config, load_config
from healer import Healer
from reporter import Reporter
from sheets import SheetsClient


# ── Structured JSON logging ───────────────────────────────────────────────────

class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts":     datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "level":  record.levelname,
            "module": record.module,
            "msg":    record.getMessage(),
        }
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


def _setup_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers = [handler]


# ── Agent ─────────────────────────────────────────────────────────────────────

class LimitlessAgent:
    """
    Main orchestrator. Owns one shared httpx.AsyncClient for connection pooling.
    Each poll cycle runs three independent checks; failures are isolated.
    """

    def __init__(self, config: Config) -> None:
        self._cfg = config
        self._stop = asyncio.Event()

        self._http: httpx.AsyncClient | None = None
        self._healer:   Healer | None = None
        self._reporter: Reporter | None = None
        self._sheets:   SheetsClient | None = None

    # ── Entry point ───────────────────────────────────────────────────────────

    async def run(self) -> None:
        """Start the agent. Blocks until SIGINT or SIGTERM."""
        self._register_signals()

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                self._cfg.http_timeout_seconds,
                connect=self._cfg.http_connect_timeout_seconds,
            ),
            follow_redirects=True,
        ) as http:
            self._http     = http
            self._healer   = Healer(self._cfg, http)
            self._reporter = Reporter(self._cfg, http)
            self._sheets   = SheetsClient(self._cfg)

            self._setup_schedules()

            logger.info(
                "LIMITLESS OS Agent started — poll_interval=%dm report_time=%s",
                self._cfg.n8n_poll_interval_minutes,
                self._cfg.report_time,
            )

            await self._reporter.send_startup_notice()

            try:
                await self._main_loop()
            finally:
                await self._reporter.send_shutdown_notice()
                logger.info("Agent shut down cleanly")

    # ── Scheduling ────────────────────────────────────────────────────────────

    def _setup_schedules(self) -> None:
        # Poll cycle every N minutes
        schedule.every(self._cfg.n8n_poll_interval_minutes).minutes.do(
            lambda: asyncio.ensure_future(self._poll_cycle())
        )
        # Daily report
        schedule.every().day.at(self._cfg.report_time).do(
            lambda: asyncio.ensure_future(self._reporter.send_daily_summary())  # type: ignore[union-attr]
        )
        logger.debug(
            "Schedules registered: poll every %dm, report at %s",
            self._cfg.n8n_poll_interval_minutes,
            self._cfg.report_time,
        )

    async def _main_loop(self) -> None:
        """
        Tick schedule every second while waiting for stop signal.
        Also run the first poll immediately on startup.
        """
        # Immediate first run
        asyncio.ensure_future(self._poll_cycle())

        while not self._stop.is_set():
            schedule.run_pending()
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                pass

    # ── Poll cycle ────────────────────────────────────────────────────────────

    async def _poll_cycle(self) -> None:
        """
        One full check across all three data sources.
        Each check is wrapped independently so failures don't cascade.
        """
        logger.info("Poll cycle starting")
        start = asyncio.get_event_loop().time()

        results = await asyncio.gather(
            self._safe_check("n8n_executions",  self._check_n8n_executions()),
            self._safe_check("dlq",             self._check_dlq()),
            self._safe_check("stuck_drafts",    self._check_stuck_drafts()),
            return_exceptions=False,
        )

        elapsed = asyncio.get_event_loop().time() - start
        fixed   = self._reporter.stats.auto_fixed  # type: ignore[union-attr]
        attn    = self._reporter.stats.needs_attention  # type: ignore[union-attr]
        logger.info(
            "Poll cycle complete in %.1fs — session: auto_fixed=%d needs_attention=%d",
            elapsed, fixed, attn,
        )

    async def _safe_check(self, name: str, coro) -> None:
        """Run a check coroutine, catching and logging any exception."""
        try:
            await coro
        except Exception as exc:
            logger.error("Check '%s' raised an unhandled error: %s", name, exc, exc_info=True)

    # ── Individual checks ─────────────────────────────────────────────────────

    async def _check_n8n_executions(self) -> None:
        """Fetch failed n8n executions and heal each one."""
        url = (
            f"{self._cfg.n8n_base_url}/api/v1/executions"
            f"?status=error&limit={self._cfg.n8n_executions_limit}"
        )
        headers = {"X-N8N-API-KEY": self._cfg.n8n_api_key}

        try:
            resp = await self._http.get(url, headers=headers)  # type: ignore[union-attr]
        except httpx.HTTPError as exc:
            logger.error("Could not reach n8n API: %s", exc)
            return

        if resp.status_code == 401:
            logger.error("n8n API returned 401 — check N8N_API_KEY")
            return
        if resp.status_code != 200:
            logger.warning("n8n API returned %d: %s", resp.status_code, resp.text[:200])
            return

        try:
            data = resp.json()
        except ValueError:
            logger.error("n8n API returned non-JSON: %s", resp.text[:200])
            return

        executions = data.get("data", data) if isinstance(data, dict) else data
        if not isinstance(executions, list):
            logger.warning("Unexpected n8n response shape: %r", type(executions))
            return

        logger.info("n8n: %d failed execution(s) to process", len(executions))

        for execution in executions:
            try:
                result = await self._healer.heal_n8n_error(execution)  # type: ignore[union-attr]
                self._reporter.record(result)  # type: ignore[union-attr]

                # Send immediate alert for non-transient errors
                if result.error_class.value in ("code_bug", "data_issue", "unknown"):
                    await self._reporter.send_alert(  # type: ignore[union-attr]
                        f"n8n execution {result.item_id}: {result.explanation}",
                        error_class=result.error_class,
                    )
            except Exception as exc:
                logger.error(
                    "Error processing execution %s: %s",
                    execution.get("id", "?"), exc, exc_info=True,
                )

    async def _check_dlq(self) -> None:
        """Fetch open DLQ rows and process each one."""
        rows = await self._sheets.get_dlq_open_errors()  # type: ignore[union-attr]

        for row in rows:
            try:
                result = await self._healer.heal_dlq_row(row)  # type: ignore[union-attr]
                self._reporter.record(result)  # type: ignore[union-attr]

                await self._reporter.send_alert(  # type: ignore[union-attr]
                    f"DLQ [{row.workflow_name}] contact {row.contact_id}: {result.explanation}",
                    error_class=result.error_class,
                )
            except Exception as exc:
                logger.error("Error processing DLQ row %s: %s", row.contact_id, exc, exc_info=True)

    async def _check_stuck_drafts(self) -> None:
        """Find stuck drafts and fire webhook to reset each one."""
        contacts = await self._sheets.get_stuck_drafts()  # type: ignore[union-attr]

        for contact in contacts:
            try:
                result = await self._healer.heal_stuck_draft(contact)  # type: ignore[union-attr]
                self._reporter.record(result)  # type: ignore[union-attr]

                if not result.success:
                    await self._reporter.send_alert(  # type: ignore[union-attr]
                        f"Could not reset stuck draft for contact {contact.contact_id}",
                        error_class=result.error_class,
                    )
            except Exception as exc:
                logger.error(
                    "Error resetting draft for %s: %s", contact.contact_id, exc, exc_info=True
                )

    # ── Signal handling ───────────────────────────────────────────────────────

    def _register_signals(self) -> None:
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._handle_shutdown)

    def _handle_shutdown(self) -> None:
        logger.info("Shutdown signal received — stopping gracefully")
        self._stop.set()


# ── Module-level logger (set up after _setup_logging is called) ───────────────
logger = logging.getLogger(__name__)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    """Load config, set up logging, run the agent."""
    try:
        cfg = load_config()
    except ValueError as exc:
        # Print raw (not JSON) for visibility before logging is set up
        print(f"[LIMITLESS OS] Configuration error:\n{exc}", file=sys.stderr)
        sys.exit(1)

    _setup_logging(cfg.log_level)

    agent = LimitlessAgent(cfg)

    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        logger.critical("Agent terminated with unhandled exception: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

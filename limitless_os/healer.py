"""
healer.py — LIMITLESS OS Self-Healing Logic
Classifies errors via Claude API and executes fix actions.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


# ── Error classification ──────────────────────────────────────────────────────

class ErrorClass(str, Enum):
    TRANSIENT   = "transient"    # network blip, timeout → auto-retry
    DATA_ISSUE  = "data_issue"   # bad input data → alert
    CODE_BUG    = "code_bug"     # workflow logic error → alert + log
    RATE_LIMIT  = "rate_limit"   # 429 / too many requests → backoff
    UNKNOWN     = "unknown"      # cannot determine → alert


# ── Result record ─────────────────────────────────────────────────────────────

@dataclass
class HealResult:
    source: str           # "n8n" | "dlq" | "tracker"
    item_id: str
    error_class: ErrorClass
    action_taken: str     # "retried" | "webhook_reset" | "backed_off" | "alerted" | "skipped"
    success: bool
    explanation: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


# ── Rate-limit tracker (module-level singleton) ────────────────────────────────

class _RateLimitTracker:
    """Suspends all n8n API calls for a configurable window after a 429."""

    def __init__(self) -> None:
        self._backoff_until: float = 0.0   # epoch seconds

    def is_backed_off(self) -> bool:
        return time.monotonic() < self._backoff_until

    def trigger_backoff(self, duration_seconds: int = 600) -> None:
        self._backoff_until = time.monotonic() + duration_seconds
        logger.warning(
            "Rate limit triggered — n8n API suspended for %d seconds", duration_seconds
        )

    def remaining_seconds(self) -> int:
        remaining = self._backoff_until - time.monotonic()
        return max(0, int(remaining))


_rate_limit = _RateLimitTracker()


# ── Healer ────────────────────────────────────────────────────────────────────

class Healer:
    """
    Orchestrates error classification and remediation.

    One shared httpx.AsyncClient is passed in (managed by the agent).
    """

    def __init__(self, config, http_client: httpx.AsyncClient) -> None:
        self._cfg = config
        self._http = http_client

    # ── Top-level dispatchers ─────────────────────────────────────────────────

    async def heal_n8n_error(self, execution: dict) -> HealResult:
        """Classify a failed n8n execution and act on it."""
        exec_id  = str(execution.get("id", "unknown"))
        wf_name  = execution.get("workflowData", {}).get("name", "unknown")
        error_msg = _extract_n8n_error(execution)

        logger.info("Healing n8n execution %s (%s): %s", exec_id, wf_name, error_msg[:120])

        error_class, explanation = await self.classify_error(
            error_message=error_msg,
            context={"source": "n8n", "workflow": wf_name, "execution_id": exec_id},
        )

        # Rate-limit check supersedes Claude's classification
        if _is_rate_limit_error(error_msg):
            error_class = ErrorClass.RATE_LIMIT

        return await self._act_on_n8n(exec_id, error_class, explanation)

    async def heal_dlq_row(self, row) -> HealResult:
        """Classify a DLQ row error. DLQ rows are never auto-retried — alert only."""
        logger.info("Healing DLQ row %s: %s", row.contact_id, row.error_message[:120])

        error_class, explanation = await self.classify_error(
            error_message=row.error_message,
            context={
                "source": "dlq",
                "workflow": row.workflow_name,
                "contact_id": row.contact_id,
                "created_at": str(row.created_at),
            },
        )

        return HealResult(
            source="dlq",
            item_id=row.contact_id,
            error_class=error_class,
            action_taken="alerted",
            success=True,
            explanation=explanation,
        )

    async def heal_stuck_draft(self, contact) -> HealResult:
        """Reset a stuck draft via n8n webhook."""
        logger.info(
            "Resetting stuck draft for contact %s (stuck since %s)",
            contact.contact_id, contact.draft_created_date,
        )

        if not self._cfg.n8n_stuck_draft_webhook_url:
            logger.warning(
                "N8N_STUCK_DRAFT_WEBHOOK_URL not set — cannot reset draft for %s",
                contact.contact_id,
            )
            return HealResult(
                source="tracker",
                item_id=contact.contact_id,
                error_class=ErrorClass.UNKNOWN,
                action_taken="skipped",
                success=False,
                explanation="Webhook URL not configured",
            )

        success = await self.reset_stuck_draft(contact.contact_id)
        return HealResult(
            source="tracker",
            item_id=contact.contact_id,
            error_class=ErrorClass.TRANSIENT,
            action_taken="webhook_reset",
            success=success,
            explanation="Sent draft-reset webhook" if success else "Webhook call failed",
        )

    # ── Actions ───────────────────────────────────────────────────────────────

    async def retry_n8n_execution(self, execution_id: str) -> bool:
        """POST /api/v1/executions/{id}/retry. Returns True on success."""
        url = f"{self._cfg.n8n_base_url}/api/v1/executions/{execution_id}/retry"
        try:
            resp = await self._http_with_retry("POST", url, headers=self._n8n_headers())
            ok = resp.status_code in (200, 201)
            if ok:
                logger.info("Retried n8n execution %s → %d", execution_id, resp.status_code)
            else:
                logger.warning(
                    "Retry of execution %s returned %d: %s",
                    execution_id, resp.status_code, resp.text[:200],
                )
            return ok
        except httpx.HTTPError as exc:
            logger.error("HTTP error retrying execution %s: %s", execution_id, exc)
            return False

    async def reset_stuck_draft(self, contact_id: str) -> bool:
        """POST contact_id to the configured n8n webhook. Returns True on success."""
        url = self._cfg.n8n_stuck_draft_webhook_url
        payload = {"contact_id": contact_id, "action": "reset_draft"}
        try:
            resp = await self._http_with_retry("POST", url, json=payload)
            ok = resp.status_code in (200, 201, 204)
            if ok:
                logger.info("Reset draft for contact %s → %d", contact_id, resp.status_code)
            else:
                logger.warning(
                    "Draft reset for %s returned %d: %s",
                    contact_id, resp.status_code, resp.text[:200],
                )
            return ok
        except httpx.HTTPError as exc:
            logger.error("HTTP error resetting draft for %s: %s", contact_id, exc)
            return False

    # ── Claude classification ─────────────────────────────────────────────────

    async def classify_error(
        self,
        error_message: str,
        context: dict,
    ) -> tuple[ErrorClass, str]:
        """
        Ask Claude to classify the error.
        Never raises — returns (UNKNOWN, reason) on any failure.
        """
        if not self._cfg.anthropic_api_key:
            return ErrorClass.UNKNOWN, "Anthropic API key not configured"

        prompt = _build_classification_prompt(error_message, context)

        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self._cfg.anthropic_api_key)
            message = await client.messages.create(
                model=self._cfg.claude_model,
                max_tokens=self._cfg.claude_max_tokens,
                system=(
                    "You are an error diagnosis assistant for an n8n automation system called "
                    "LIMITLESS OS. Classify the error as exactly one of: "
                    "transient | data_issue | code_bug | rate_limit | unknown.\n"
                    "Return ONLY this format — nothing else:\n"
                    "CLASSIFICATION: <class>\n"
                    "EXPLANATION: <one concise sentence>"
                ),
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text.strip()
            return _parse_classification(raw)

        except ImportError:
            logger.error("anthropic SDK not installed — pip install anthropic")
            return ErrorClass.UNKNOWN, "anthropic SDK not installed"
        except Exception as exc:
            logger.warning("Claude API error: %s", exc)
            # Fall back to heuristic classification
            return _heuristic_classify(error_message)

    # ── HTTP helper ───────────────────────────────────────────────────────────

    async def _http_with_retry(
        self,
        method: str,
        url: str,
        max_attempts: int | None = None,
        **kwargs,
    ) -> httpx.Response:
        """
        Execute an HTTP request with exponential backoff + jitter.
        Parses Retry-After header on 429.
        Raises httpx.HTTPError after all attempts are exhausted.
        """
        attempts = max_attempts or self._cfg.http_max_retries
        last_exc: Exception | None = None

        for attempt in range(attempts):
            try:
                resp = await self._http.request(method, url, **kwargs)

                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 60))
                    _rate_limit.trigger_backoff(retry_after)
                    raise httpx.HTTPStatusError(
                        f"429 rate limited (Retry-After: {retry_after}s)",
                        request=resp.request,
                        response=resp,
                    )

                return resp

            except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as exc:
                last_exc = exc
                if attempt < attempts - 1:
                    wait = min(2 ** attempt + random.uniform(0, 1), 30)
                    logger.warning(
                        "%s %s attempt %d/%d failed (%s) — retrying in %.1fs",
                        method, url, attempt + 1, attempts, exc, wait,
                    )
                    await asyncio.sleep(wait)
                else:
                    logger.error(
                        "%s %s failed after %d attempts: %s", method, url, attempts, exc
                    )

        raise httpx.HTTPError(f"All {attempts} attempts failed for {method} {url}") from last_exc

    def _n8n_headers(self) -> dict[str, str]:
        return {"X-N8N-API-KEY": self._cfg.n8n_api_key, "Content-Type": "application/json"}


# ── Action dispatcher ─────────────────────────────────────────────────────────

    async def _act_on_n8n(
        self,
        exec_id: str,
        error_class: ErrorClass,
        explanation: str,
    ) -> HealResult:
        """Map classification to action for n8n executions."""

        if error_class == ErrorClass.RATE_LIMIT:
            _rate_limit.trigger_backoff(600)
            return HealResult(
                source="n8n",
                item_id=exec_id,
                error_class=error_class,
                action_taken="backed_off",
                success=True,
                explanation=explanation,
            )

        if error_class == ErrorClass.TRANSIENT:
            if _rate_limit.is_backed_off():
                logger.info(
                    "Skipping retry of %s — rate limit backoff (%ds remaining)",
                    exec_id, _rate_limit.remaining_seconds(),
                )
                return HealResult(
                    source="n8n",
                    item_id=exec_id,
                    error_class=error_class,
                    action_taken="skipped",
                    success=False,
                    explanation=f"Skipped: rate limit backoff active ({_rate_limit.remaining_seconds()}s remaining)",
                )

            success = await self.retry_n8n_execution(exec_id)
            return HealResult(
                source="n8n",
                item_id=exec_id,
                error_class=error_class,
                action_taken="retried",
                success=success,
                explanation=explanation,
            )

        # data_issue / code_bug / unknown → alert only
        return HealResult(
            source="n8n",
            item_id=exec_id,
            error_class=error_class,
            action_taken="alerted",
            success=True,
            explanation=explanation,
        )


# ── Private helpers ────────────────────────────────────────────────────────────

def _extract_n8n_error(execution: dict) -> str:
    """Pull the most useful error string out of an n8n execution object."""
    # n8n stores errors in various locations depending on version
    for path in [
        ["data", "resultData", "error", "message"],
        ["data", "resultData", "runData"],
        ["error", "message"],
        ["stoppedAt"],
    ]:
        node = execution
        for key in path:
            if not isinstance(node, dict):
                break
            node = node.get(key)
        if isinstance(node, str) and node:
            return node

    return json.dumps(execution.get("data", {}))[:500]


def _is_rate_limit_error(message: str) -> bool:
    lower = message.lower()
    return any(phrase in lower for phrase in [
        "rate limit", "too many requests", "429", "quota exceeded",
        "throttl", "ratelimit",
    ])


def _build_classification_prompt(error_message: str, context: dict) -> str:
    ctx_str = json.dumps(context, ensure_ascii=False, indent=2)
    return (
        f"Error message:\n{error_message}\n\n"
        f"Context:\n{ctx_str}"
    )


def _parse_classification(raw: str) -> tuple[ErrorClass, str]:
    """Parse Claude's structured response. Falls back to UNKNOWN on malformed output."""
    classification = ErrorClass.UNKNOWN
    explanation = raw

    for line in raw.splitlines():
        line = line.strip()
        if line.upper().startswith("CLASSIFICATION:"):
            val = line.split(":", 1)[1].strip().lower()
            try:
                classification = ErrorClass(val)
            except ValueError:
                logger.warning("Claude returned unknown class %r — using UNKNOWN", val)
                classification = ErrorClass.UNKNOWN
        elif line.upper().startswith("EXPLANATION:"):
            explanation = line.split(":", 1)[1].strip()

    return classification, explanation


def _heuristic_classify(message: str) -> tuple[ErrorClass, str]:
    """Rule-based fallback when Claude is unavailable."""
    lower = message.lower()
    if _is_rate_limit_error(message):
        return ErrorClass.RATE_LIMIT, "Rate limit detected (heuristic)"
    if any(w in lower for w in ["timeout", "connection", "network", "econnreset", "socket"]):
        return ErrorClass.TRANSIENT, "Network/timeout error (heuristic)"
    if any(w in lower for w in ["syntax", "typeerror", "referenceerror", "undefined", "cannot read"]):
        return ErrorClass.CODE_BUG, "Code error detected (heuristic)"
    if any(w in lower for w in ["invalid", "missing field", "required", "not found", "null"]):
        return ErrorClass.DATA_ISSUE, "Data issue detected (heuristic)"
    return ErrorClass.UNKNOWN, "Could not classify (heuristic fallback)"

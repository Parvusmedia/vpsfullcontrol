"""Classify Unipile LinkedIn invite errors for the shared NocoDB action log.

Used by prospeccion unipile-drain pipelines and n8n Step2 processors.
``already_invited_recently`` is terminal (do not retry). Shared daily/hourly
caps stay as ``limit_reached``. True provider throttling stays retryable.
"""

from __future__ import annotations

from typing import Literal

Outcome = Literal[
    "success",
    "already_invited",
    "invalid_provider",
    "provider_limit",
    "rate_limit",
    "failed",
]

_ALREADY_INVITED_NEEDLES = (
    "already_invited_recently",
    "already_invited",
    "should delay new invitation",
    "invitation has already been sent",
)

_INVALID_PROVIDER_NEEDLES = (
    "user id does not match",
    "does not match provider's expected format",
    "does not match provider",
)

_RATE_LIMIT_NEEDLES = (
    "rate limit",
    "too many",
    "throttl",
)


def haystack(http_status: int | None, *parts: object) -> str:
    bits = [str(http_status or "")]
    for part in parts:
        if part is None:
            continue
        bits.append(str(part))
    return " ".join(bits).lower()


def classify_invite_error(
    *,
    http_status: int | None = None,
    error_type: str = "",
    error_code: str = "",
    error_message: str = "",
    title: str = "",
    detail: str = "",
) -> Outcome:
    """Map a Unipile HTTP error to a queue outcome."""
    hay = haystack(http_status, error_type, error_code, error_message, title, detail)
    status = int(http_status or 0)

    if any(n in hay for n in _ALREADY_INVITED_NEEDLES):
        return "already_invited"

    if status == 400 and any(n in hay for n in _INVALID_PROVIDER_NEEDLES):
        return "invalid_provider"

    if status == 429 or any(n in hay for n in _RATE_LIMIT_NEEDLES):
        return "rate_limit"

    # Remaining 422 / cannot_resend / invitation-limit → pause and retry later.
    if (
        status == 422
        or "cannot_resend" in hay
        or ("limit" in hay and "invit" in hay)
    ):
        return "provider_limit"

    if status >= 400:
        return "failed"
    return "success"


def log_status_for_outcome(outcome: Outcome) -> str:
    return {
        "success": "success",
        "already_invited": "skipped",
        "invalid_provider": "skipped",
        "provider_limit": "limit_reached",
        "rate_limit": "limit_reached",
        "failed": "failed",
    }[outcome]


def should_retry(outcome: Outcome) -> bool:
    return outcome in {"provider_limit", "rate_limit", "failed"}


def should_pause_account(outcome: Outcome) -> bool:
    return outcome in {"provider_limit", "rate_limit"}


def mark_source_sent(outcome: Outcome) -> bool:
    """Close the source row so unipile-drain does not pick it again."""
    return outcome in {"success", "already_invited", "invalid_provider"}

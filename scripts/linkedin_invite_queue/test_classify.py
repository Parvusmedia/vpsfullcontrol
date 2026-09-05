#!/usr/bin/env python3
"""Unit tests for Unipile invite error classification."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from classify import (
    classify_invite_error,
    log_status_for_outcome,
    mark_source_sent,
    should_pause_account,
    should_retry,
)


class ClassifyInviteErrorTests(unittest.TestCase):
    def test_already_invited_json_422(self) -> None:
        outcome = classify_invite_error(
            http_status=422,
            error_type="errors/already_invited_recently",
            error_message=(
                '{"status":422,"type":"errors/already_invited_recently",'
                '"title":"Should delay new invitation to this recipient",'
                '"detail":"An invitation has already been sent recently to this recipient. '
                'Please try again later."}'
            ),
        )
        self.assertEqual(outcome, "already_invited")
        self.assertEqual(log_status_for_outcome(outcome), "skipped")
        self.assertTrue(mark_source_sent(outcome))
        self.assertFalse(should_retry(outcome))
        self.assertFalse(should_pause_account(outcome))

    def test_already_invited_httpx_wrapper_not_provider_limit(self) -> None:
        outcome = classify_invite_error(
            http_status=None,
            error_message=(
                "Client error '422 Unprocessable Entity' for url "
                "'https://api46.unipile.com:17682/api/v1/users/invite'\n"
                "For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/422"
            ),
        )
        # Wrapper alone has no already_invited needle; 422 in URL/status text is not
        # enough. Callers should classify the JSON body, not the httpx duplicate.
        self.assertNotEqual(outcome, "already_invited")

    def test_already_invited_title_without_type(self) -> None:
        outcome = classify_invite_error(
            http_status=422,
            title="Should delay new invitation to this recipient",
            detail="An invitation has already been sent recently to this recipient.",
        )
        self.assertEqual(outcome, "already_invited")

    def test_invalid_provider_id(self) -> None:
        outcome = classify_invite_error(
            http_status=400,
            error_type="errors/invalid_parameters",
            error_message="User ID does not match provider's expected format.",
        )
        self.assertEqual(outcome, "invalid_provider")
        self.assertTrue(mark_source_sent(outcome))
        self.assertFalse(should_retry(outcome))

    def test_rate_limit_429(self) -> None:
        outcome = classify_invite_error(http_status=429, error_message="Too many requests")
        self.assertEqual(outcome, "rate_limit")
        self.assertTrue(should_retry(outcome))
        self.assertTrue(should_pause_account(outcome))
        self.assertFalse(mark_source_sent(outcome))

    def test_generic_422_still_provider_limit(self) -> None:
        outcome = classify_invite_error(
            http_status=422,
            error_type="errors/cannot_resend_yet",
            error_message="cannot_resend_yet",
        )
        self.assertEqual(outcome, "provider_limit")
        self.assertTrue(should_retry(outcome))
        self.assertTrue(should_pause_account(outcome))
        self.assertFalse(mark_source_sent(outcome))

    def test_disconnected_account_is_retryable_failure(self) -> None:
        outcome = classify_invite_error(
            http_status=401,
            error_type="errors/disconnected_account",
            title="Disconnected account",
        )
        self.assertEqual(outcome, "failed")
        self.assertTrue(should_retry(outcome))
        self.assertFalse(mark_source_sent(outcome))

    def test_daily_limit_message_is_not_unipile_http(self) -> None:
        # Internal gate messages are not classified here; this only covers Unipile HTTP.
        outcome = classify_invite_error(
            http_status=None,
            error_message="Daily limit reached: 15/15",
        )
        self.assertEqual(outcome, "success")


if __name__ == "__main__":
    unittest.main()

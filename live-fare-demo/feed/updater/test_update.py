#!/usr/bin/env python3
"""Unit tests for the live-fare updater (stdlib only)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import update as updater


class UpdaterTests(unittest.TestCase):
    def test_jitter_stays_within_bounds(self) -> None:
        for _ in range(200):
            price = updater.jitter_price(379, 349, 429)
            self.assertGreaterEqual(price, 349)
            self.assertLessEqual(price, 429)

    def test_atomic_write_replaces_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "MAD.json"
            with mock.patch.object(updater, "PUBLIC_DIR", Path(tmp)):
                updater.atomic_write_json(target, {"ok": True})
                self.assertTrue(target.is_file())
                self.assertFalse((Path(tmp) / "MAD.tmp.json").exists())
                self.assertEqual(json.loads(target.read_text())["ok"], True)

    def test_generate_feed_shape(self) -> None:
        source = {
            "origin": "MAD",
            "deeplink_base": "https://example.com/book",
            "fares": [
                {
                    "destination": "RUH",
                    "destination_name": "Riyadh",
                    "month": "2026-10",
                    "price": 379,
                    "currency": "EUR",
                    "min_price": 349,
                    "max_price": 429,
                }
            ],
        }
        feed = updater.generate_feed(source, None, jitter=False)
        self.assertEqual(feed["origin"], "MAD")
        self.assertIn("updated_at", feed)
        self.assertEqual(len(feed["fares"]), 1)
        fare = feed["fares"][0]
        self.assertEqual(fare["price"], 379)
        self.assertEqual(fare["destination"], "RUH")
        self.assertIn("origin=MAD", fare["deeplink"])
        self.assertIn("destination=RUH", fare["deeplink"])
        self.assertIn("month=2026-10", fare["deeplink"])
        self.assertNotIn("min_price", fare)

    def test_missing_combo_not_invented(self) -> None:
        source = {"origin": "MAD", "fares": []}
        feed = updater.generate_feed(source, None, jitter=False)
        self.assertEqual(feed["fares"], [])


if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parent)
    unittest.main()

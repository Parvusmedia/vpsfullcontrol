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


SOURCE = {
    "deeplink_base": "https://example.com/book",
    "months": ["2026-10", "2026-11"],
    "origins": [
        {"code": "JED", "name": "Jeddah", "country": "SA", "country_name": "Saudi Arabia", "currency": "SAR"}
    ],
    "routes": [
        {
            "origin": "JED",
            "destination": "RUH",
            "destination_name": "Riyadh",
            "currency": "SAR",
            "price": 380,
            "min_price": 320,
            "max_price": 450,
        }
    ],
}


class UpdaterTests(unittest.TestCase):
    def test_jitter_stays_within_bounds(self) -> None:
        for _ in range(200):
            price = updater.jitter_price(380, 320, 450)
            self.assertGreaterEqual(price, 320)
            self.assertLessEqual(price, 450)

    def test_atomic_write_replaces_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "network.json"
            with mock.patch.object(updater, "PUBLIC_DIR", Path(tmp)):
                updater.atomic_write_json(target, {"ok": True})
                self.assertTrue(target.is_file())
                self.assertFalse((Path(tmp) / "network.tmp.json").exists())
                self.assertEqual(json.loads(target.read_text())["ok"], True)

    def test_generate_network_expands_months(self) -> None:
        feed = updater.generate_network(SOURCE, None, jitter=False)
        self.assertEqual(len(feed["fares"]), 2)
        self.assertEqual(feed["fares"][0]["origin"], "JED")
        self.assertEqual(feed["fares"][0]["destination"], "RUH")
        self.assertIn("B_LOCATION=JED", feed["fares"][0]["deeplink"])
        self.assertIn("E_LOCATION=RUH", feed["fares"][0]["deeplink"])
        self.assertIn("DATE_1=2026-10-15", feed["fares"][0]["deeplink"])
        self.assertIn("trip_type=OW", feed["fares"][0]["deeplink"])
        self.assertNotIn("min_price", feed["fares"][0])
        oct_fare = next(f for f in feed["fares"] if f["month"] == "2026-10")
        self.assertEqual(oct_fare["price"], 380)
        self.assertEqual(oct_fare["currency"], "SAR")

    def test_split_origin_feeds(self) -> None:
        feed = updater.generate_network(SOURCE, None, jitter=False)
        split = updater.split_origin_feeds(feed)
        self.assertIn("JED", split)
        self.assertEqual(split["JED"]["origin"], "JED")
        self.assertNotIn("origin", split["JED"]["fares"][0])

    def test_build_deeplink_uses_saudia_wds_params(self) -> None:
        url = updater.build_deeplink(
            "https://www.saudia.com/booking", "DXB", "JED", "2026-11"
        )
        self.assertEqual(
            url,
            "https://www.saudia.com/booking?B_LOCATION=DXB&E_LOCATION=JED&trip_type=OW&DATE_1=2026-11-15T00%3A00%3A00",
        )

    def test_missing_combo_not_invented(self) -> None:
        empty = {"origins": [], "routes": [], "months": ["2026-10"]}
        feed = updater.generate_network(empty, None, jitter=False)
        self.assertEqual(feed["fares"], [])


if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parent)
    unittest.main()

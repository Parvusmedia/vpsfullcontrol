#!/usr/bin/env python3
"""Smoke tests for meta_ads helpers (no network)."""

import os
import unittest

from meta_ads import DRAFT_NAME_PREFIX, MetaScopeError, _ad_account_path, _assert_scope_page_id, _draft_name


class MetaAdsHelpersTest(unittest.TestCase):
    def test_ad_account_path(self) -> None:
        self.assertEqual(_ad_account_path("476956206434765"), "/act_476956206434765")
        self.assertEqual(_ad_account_path("act_476956206434765"), "/act_476956206434765")

    def test_draft_name(self) -> None:
        self.assertTrue(_draft_name("Foo").startswith(DRAFT_NAME_PREFIX))
        self.assertEqual(_draft_name(f"{DRAFT_NAME_PREFIX} Foo"), f"{DRAFT_NAME_PREFIX} Foo")


    def test_scope_blocks_foreign_page(self) -> None:
        os.environ["META_SCOPE"] = "digitanimal"
        os.environ["META_CLIENT_BUSINESS_ID"] = "461966487998679"
        with self.assertRaises(MetaScopeError):
            _assert_scope_page_id("114588839232748")  # Prosegur


if __name__ == "__main__":
    unittest.main()

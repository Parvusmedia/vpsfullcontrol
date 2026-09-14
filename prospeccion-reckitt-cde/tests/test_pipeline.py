from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reckitt.config import BLOCKED_UNIPILE_ACCOUNT_IDS, EMILIANO_CDE_UNIPILE_ACCOUNT_ID, ReckittConfig
from reckitt.csv_leads import load_csv, summarize_leads
from reckitt.messages import build_connection_message, compose_row_messages
from reckitt.smartlead import EMAIL_1_SUBJECT, EMAIL_2_SUBJECT, EMAIL_3_SUBJECT, campaign_sequence_spec

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample.csv"


class CsvMappingTests(unittest.TestCase):
    def test_maps_work_email_and_fields(self) -> None:
        leads = load_csv(FIXTURE)
        self.assertEqual(len(leads), 3)
        first = leads[0]
        self.assertEqual(first["first_name"], "Ada")
        self.assertEqual(first["last_name"], "Lovelace")
        self.assertEqual(first["email"], "ada.lovelace@reckitt.com")
        self.assertEqual(first["company_name"], "Reckitt")
        self.assertEqual(first["linkedin_url"], "https://www.linkedin.com/in/ada-lovelace-test")
        self.assertEqual(first["job_title"], "Digital Media Manager")
        self.assertEqual(first["location"], "London, United Kingdom")
        self.assertEqual(first["relevante"], "Sí")

        stats = summarize_leads(leads)
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["with_email"], 2)
        self.assertEqual(stats["without_email"], 1)
        self.assertEqual(stats["email_domains"], ["reckitt.com"])

    def test_missing_email_keeps_icypeas_miss(self) -> None:
        leads = load_csv(FIXTURE)
        hopper = next(x for x in leads if x["first_name"] == "Grace")
        self.assertEqual(hopper["email"], "")
        self.assertEqual(hopper["status"], "icypeas_miss")
        self.assertTrue(hopper["linkedin_url"].endswith("/grace-hopper-test"))


class CopyTests(unittest.TestCase):
    def test_invite_note_under_175(self) -> None:
        lead = {"first_name": "Nattaphan", "company_name": "Reckitt"}
        note = build_connection_message(lead)
        self.assertLessEqual(len(note), 175)
        self.assertIn("Nattaphan", note)
        self.assertIn("weather", note.lower())
        self.assertIn("Google Trends", note)
        self.assertTrue(note.startswith("Hi Nattaphan, I'm Emiliano from Parvus Media."))
        msgs = compose_row_messages(lead)
        self.assertEqual(msgs["mensaje_estado"], "Pendiente confirmar")
        self.assertIn("Google Trends", msgs["followup_message"])

    def test_sequence_has_three_en_subjects(self) -> None:
        spec = campaign_sequence_spec()
        self.assertEqual(spec["status_at_create"], "PAUSED")
        self.assertEqual(len(spec["steps"]), 3)
        self.assertIn("7-day", EMAIL_1_SUBJECT)
        self.assertTrue(EMAIL_2_SUBJECT.startswith("Re:"))
        self.assertTrue(EMAIL_3_SUBJECT.startswith("Re:"))
        self.assertEqual(spec["language"], "en")


class SeatTests(unittest.TestCase):
    def test_blocks_nextconvers_seat(self) -> None:
        cfg = ReckittConfig(unipile_account_id=next(iter(BLOCKED_UNIPILE_ACCOUNT_IDS)))
        with self.assertRaises(RuntimeError):
            cfg.assert_unipile_seat()

    def test_default_emiliano_seat_ok(self) -> None:
        cfg = ReckittConfig(unipile_account_id=EMILIANO_CDE_UNIPILE_ACCOUNT_ID)
        cfg.assert_unipile_seat()


class StoreTests(unittest.TestCase):
    def test_upsert_relevantes(self) -> None:
        import reckitt.config as cfg_mod
        import reckitt.store as st

        leads = load_csv(FIXTURE)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "leads.json"
            old = cfg_mod.LEADS_PATH
            cfg_mod.LEADS_PATH = path
            try:
                result = st.upsert_leads(leads)
                self.assertEqual(result["created"], 3)
                rows = st.list_relevantes(limit=10)
                self.assertEqual(len(rows), 3)
                hopper = next(x for x in rows if x["first_name"] == "Grace")
                st.patch_record(int(hopper["Id"]), {"status": "hold", "unipile_status": "queued"})
                still = st.list_relevantes(limit=10)
                self.assertEqual(len(still), 2)
                queue = st.list_unipile_queue(limit=10)
                self.assertEqual(len(queue), 1)
            finally:
                cfg_mod.LEADS_PATH = old


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from consultant_radar.cli import main


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_companies_lists_ids(self) -> None:
        from io import StringIO
        from unittest.mock import patch

        buf = StringIO()
        with patch("sys.stdout", buf):
            rc = main(["--companies", str(ROOT / "config" / "companies.json"), "companies"])
        self.assertEqual(rc, 0)
        text = buf.getvalue()
        self.assertIn("accenture", text)
        self.assertIn("deloitte-es", text)
        self.assertIn("kpmg-es", text)

    def test_scan_with_stub_source(self) -> None:
        from consultant_radar import cli
        from consultant_radar.models import Job
        from consultant_radar.sources.phenom import PhenomSource

        class Stub(PhenomSource):
            def fetch(self, company):
                return [
                    Job(
                        company_id=company["id"],
                        company_name=company["name"],
                        source="phenom",
                        source_id="1",
                        title="Adobe Campaign Consultant",
                        location="Madrid",
                        url="https://example.com/1",
                        brands=tuple(company.get("brands") or []),
                    ),
                    Job(
                        company_id=company["id"],
                        company_name=company["name"],
                        source="phenom",
                        source_id="2",
                        title="Tax Manager Transfer Pricing",
                        location="Madrid",
                        url="https://example.com/2",
                    ),
                ]

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db = Path(tmp.name) / "radar.sqlite"

        original = cli.build_registry

        def fake_registry(**kwargs):
            registry = original(**kwargs)
            registry["phenom"] = Stub()
            return registry

        cli.build_registry = fake_registry  # type: ignore[assignment]
        self.addCleanup(setattr, cli, "build_registry", original)

        from io import StringIO
        from unittest.mock import patch

        buf = StringIO()
        with patch("sys.stdout", buf), patch("sys.stderr", StringIO()):
            rc = main(
                [
                    "--db",
                    str(db),
                    "scan",
                    "--company",
                    "deloitte-es",
                    "--json",
                ]
            )
        self.assertEqual(rc, 0)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["seen"], 2)
        self.assertEqual(payload["matched"], 1)
        self.assertEqual(payload["new"], 1)
        self.assertEqual(payload["jobs"][0]["title"], "Adobe Campaign Consultant")


@unittest.skipUnless(os.environ.get("CONSULTANT_RADAR_LIVE") == "1", "live ATS scan")
class LiveScanTests(unittest.TestCase):
    def test_deloitte_es_returns_jobs(self) -> None:
        from consultant_radar.sources.phenom import PhenomSource

        jobs = PhenomSource().fetch(
            {
                "id": "deloitte-es",
                "name": "Deloitte",
                "brands": ["Deloitte Digital"],
                "list_url": "https://empleo.es.deloitte.com/search-jobs",
                "base_url": "https://empleo.es.deloitte.com",
                "max_pages": 1,
            }
        )
        self.assertGreater(len(jobs), 5)
        self.assertTrue(any(job.title for job in jobs))


if __name__ == "__main__":
    unittest.main()

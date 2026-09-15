from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from consultant_radar.models import Job
from consultant_radar.store import Store


def job(source_id: str, title: str = "Adobe Lead") -> Job:
    return Job(
        company_id="deloitte-es",
        company_name="Deloitte",
        source="phenom",
        source_id=source_id,
        title=title,
        location="Madrid",
        url=f"https://empleo.es.deloitte.com/job/{source_id}",
        brands=("Deloitte Digital",),
    )


class StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "radar.sqlite")

    def tearDown(self) -> None:
        self.store.close()
        self.tmp.cleanup()

    def test_insert_then_update_not_new(self) -> None:
        scan1 = self.store.start_scan()
        first = self.store.upsert_jobs(scan1, [(job("100"), ["adobe"])], now="2026-09-03T10:00:00+00:00")
        self.store.finish_scan(scan1, seen=1, matched=1, new=first["new"])
        self.assertEqual(first["new"], 1)

        scan2 = self.store.start_scan()
        second = self.store.upsert_jobs(scan2, [(job("100", "Adobe Lead ES"), ["adobe"])], now="2026-09-03T11:00:00+00:00")
        self.store.finish_scan(scan2, seen=1, matched=1, new=second["new"])
        self.assertEqual(second["new"], 0)

        listed = self.store.list_jobs(only_new=True, scan_id=scan2)
        self.assertEqual(listed, [])
        all_rows = self.store.list_jobs(limit=10)
        self.assertEqual(len(all_rows), 1)
        self.assertEqual(all_rows[0]["title"], "Adobe Lead ES")
        self.assertEqual(all_rows[0]["first_seen_at"], "2026-09-03T10:00:00+00:00")
        self.assertEqual(all_rows[0]["last_seen_at"], "2026-09-03T11:00:00+00:00")

    def test_new_on_second_scan(self) -> None:
        scan1 = self.store.start_scan()
        self.store.upsert_jobs(scan1, [(job("100"), ["adobe"])])
        scan2 = self.store.start_scan()
        stats = self.store.upsert_jobs(scan2, [(job("100"), ["adobe"]), (job("200"), ["digital"])])
        self.assertEqual(stats["new"], 1)
        listed = self.store.list_jobs(only_new=True, scan_id=scan2)
        self.assertEqual([row["uid"] for row in listed], ["deloitte-es:phenom:200"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from consultant_radar.match import Filters, classify, is_excluded, matched_keywords
from consultant_radar.models import Job


def job(**kwargs) -> Job:
    defaults = dict(
        company_id="accenture",
        company_name="Accenture",
        source="workday",
        source_id="1",
        title="Adobe Experience Manager Lead",
        location="Madrid",
        url="https://example.com/job/1",
        brands=("Accenture Song",),
    )
    defaults.update(kwargs)
    return Job(**defaults)


class MatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.filters = Filters(
            include_keywords=("adobe", "song", "martech", "digital"),
            exclude_keywords=("tax", "audit", "intern"),
            exclude_title_prefixes=("US E - Tax",),
        )

    def test_include_keyword(self) -> None:
        hits = matched_keywords(job(), self.filters)
        self.assertIn("adobe", hits)

    def test_song_from_title_not_brand(self) -> None:
        hits = matched_keywords(
            job(title="Creative Director", location="New York", brands=("Accenture Song",)),
            self.filters,
        )
        self.assertEqual(hits, [])
        hits = matched_keywords(
            job(title="Accenture Song Designer", location="Madrid"),
            self.filters,
        )
        self.assertIn("song", hits)

    def test_utm_campaign_in_url_is_ignored(self) -> None:
        hits = matched_keywords(
            job(
                title="Ingeniero de Pruebas",
                location="Mexico",
                url="https://jobs.example.com/job/1?utm_campaign=J2W_RSS",
                brands=(),
            ),
            Filters(
                include_keywords=("campaign",),
                exclude_keywords=(),
                exclude_title_prefixes=(),
            ),
        )
        self.assertEqual(hits, [])

    def test_exclude_tax_not_international(self) -> None:
        self.assertTrue(is_excluded(job(title="Transfer Pricing Tax Manager"), self.filters))
        kept = classify(
            [job(title="International Digital Commerce Lead", source_id="2")],
            self.filters,
        )
        self.assertEqual(len(kept), 1)

    def test_intern_word_boundary(self) -> None:
        self.assertTrue(is_excluded(job(title="Marketing Intern Madrid"), self.filters))
        kept = classify(
            [job(title="International Martech Partner", source_id="3")],
            self.filters,
        )
        self.assertEqual(len(kept), 1)

    def test_require_include(self) -> None:
        sap = job(title="SAP FICO Consultant", location="Bogota", brands=())
        self.assertEqual(classify([sap], self.filters), [])
        kept = classify([sap], self.filters, require_include=False)
        self.assertEqual(len(kept), 1)

    def test_skips_blank_title(self) -> None:
        kept = classify([job(title="  ", location="Madrid")], self.filters)
        self.assertEqual(kept, [])


if __name__ == "__main__":
    unittest.main()

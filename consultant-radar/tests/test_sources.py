from __future__ import annotations

import unittest

from consultant_radar.sources.phenom import parse_phenom_jobs
from consultant_radar.sources.rss import parse_rss_jobs
from consultant_radar.sources.workday import WorkdaySource


COMPANY = {
    "id": "deloitte-es",
    "name": "Deloitte",
    "brands": ["Deloitte Digital"],
    "list_url": "https://empleo.es.deloitte.com/search-jobs",
    "base_url": "https://empleo.es.deloitte.com",
}


class PhenomParseTests(unittest.TestCase):
    def test_dedupes_job_links(self) -> None:
        html = """
        <html><body>
          <a href="/job/Madrid-Adobe-Campaign-Consultant/1382072433/">
            Adobe Campaign Consultant
          </a>
          <a href="/job/Madrid-Adobe-Campaign-Consultant/1382072433/">Adobe Campaign Consultant</a>
          <a href="/search-jobs">not a job</a>
        </body></html>
        """
        jobs = parse_phenom_jobs(html, COMPANY)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].source_id, "1382072433")
        self.assertEqual(jobs[0].title, "Adobe Campaign Consultant")
        self.assertEqual(jobs[0].location, "Madrid")
        self.assertTrue(jobs[0].url.endswith("/job/Madrid-Adobe-Campaign-Consultant/1382072433/"))


class RssParseTests(unittest.TestCase):
    def test_skips_empty_placeholder(self) -> None:
        xml = """<?xml version="1.0"?>
        <rss version="2.0"><channel>
          <item>
            <title>No jobs currently available - Check out our other opportunities.</title>
            <link>https://jobs.capgemini.com</link>
            <guid>0</guid>
          </item>
          <item>
            <title>Digital Marketing Manager (Madrid, ES)</title>
            <link>https://jobs.capgemini.com/job/123</link>
            <guid>https://jobs.capgemini.com/job/123</guid>
            <pubDate>Thu, 3 Sep 2026 00:00:00 GMT</pubDate>
          </item>
        </channel></rss>
        """
        jobs = parse_rss_jobs(xml, {"id": "capgemini", "name": "Capgemini", "brands": ["Capgemini"]}, "rss")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].source_id, "123")
        self.assertEqual(jobs[0].location, "Madrid, ES")


class WorkdaySourceTests(unittest.TestCase):
    def test_paginates_and_maps_fields(self) -> None:
        pages = [
            {
                "total": 25,
                "jobPostings": [
                    {
                        "title": "Accenture Song Designer",
                        "externalPath": "/job/Madrid/Song-Designer_R1",
                        "postedOn": "Posted Today",
                        "bulletFields": ["R1", "Madrid"],
                    }
                ]
                + [
                    {
                        "title": f"Role {i}",
                        "externalPath": f"/job/Madrid/Role_{i}",
                        "bulletFields": [str(i), "Madrid"],
                    }
                    for i in range(19)
                ],
            },
            {
                "total": 25,
                "jobPostings": [
                    {
                        "title": "Last role",
                        "externalPath": "/job/London/Last_R99",
                        "bulletFields": ["R99", "London"],
                    }
                ],
            },
        ]
        calls = []

        def fake_json(url, method="GET", json_body=None):
            calls.append((url, method, json_body))
            return pages[len(calls) - 1]

        source = WorkdaySource(request_json=fake_json)
        jobs = source.fetch(
            {
                "id": "accenture",
                "name": "Accenture",
                "brands": ["Accenture Song"],
                "host": "accenture.wd103.myworkdayjobs.com",
                "tenant": "accenture",
                "site": "AccentureCareers",
                "search_texts": ["Song"],
                "max_pages": 5,
            }
        )
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][2]["offset"], 0)
        self.assertEqual(calls[1][2]["offset"], 20)
        song = next(j for j in jobs if j.source_id == "R1")
        self.assertEqual(song.title, "Accenture Song Designer")
        self.assertIn("AccentureCareers/job/Madrid/Song-Designer_R1", song.url)
        self.assertEqual(len(jobs), 21)


if __name__ == "__main__":
    unittest.main()

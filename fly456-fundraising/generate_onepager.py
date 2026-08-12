#!/usr/bin/env python3
"""PDF one-pager aligned with named-monitoring + Economy/Business positioning."""

from pathlib import Path

from fpdf import FPDF

OUT = Path(__file__).resolve().parent / "Fly456_Kima_OnePager.pdf"
OUT_ROOT = Path(__file__).resolve().parents[1] / "Fly456_Kima_OnePager.pdf"
OUT_ART = Path("/opt/cursor/artifacts/Fly456_Kima_OnePager.pdf")
FONT_REG = "/tmp/Roboto-Regular.ttf"
FONT_BOLD = "/tmp/Roboto-Bold.ttf"

NAVY = (15, 30, 45)
TEAL = (0, 110, 130)
ACCENT = (230, 120, 40)
LIGHT = (246, 248, 250)
MUTED = (95, 110, 120)
WHITE = (255, 255, 255)
DARK = (25, 35, 45)


class Deck(FPDF):
    def __init__(self):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.set_auto_page_break(auto=False)
        self.add_font("Roboto", "", FONT_REG)
        self.add_font("Roboto", "B", FONT_BOLD)
        self.n = 0
        self.total = 6

    def slide(self, eyebrow, title):
        self.add_page()
        self.n += 1
        self.set_fill_color(*TEAL)
        self.rect(0, 0, 6, 210, "F")
        self.set_fill_color(*LIGHT)
        self.rect(6, 0, 291, 12, "F")
        self.set_font("Roboto", "", 9)
        self.set_text_color(*MUTED)
        self.set_xy(14, 3)
        self.cell(200, 6, "Fly456  ·  Pre-seed note for Kima Ventures")
        self.set_xy(240, 3)
        self.cell(40, 6, f"{self.n}/{self.total}", align="R")
        self.set_font("Roboto", "B", 10)
        self.set_text_color(*TEAL)
        self.set_xy(14, 20)
        self.cell(0, 6, eyebrow.upper())
        self.set_font("Roboto", "B", 22)
        self.set_text_color(*NAVY)
        self.set_xy(14, 28)
        self.multi_cell(270, 9, title)
        return self.get_y() + 4

    def bullets(self, y, lines):
        self.set_font("Roboto", "", 12)
        self.set_text_color(*DARK)
        for line in lines:
            self.set_xy(14, y)
            self.cell(5, 7, "-")
            self.set_xy(20, y)
            self.multi_cell(260, 7, line)
            y = self.get_y() + 2
        return y

    def box(self, x, y, w, h, title, lines):
        self.set_fill_color(*LIGHT)
        self.rect(x, y, w, h, "F")
        self.set_fill_color(*TEAL)
        self.rect(x, y, w, 1.2, "F")
        self.set_font("Roboto", "B", 12)
        self.set_text_color(*NAVY)
        self.set_xy(x + 4, y + 5)
        self.cell(w - 8, 6, title)
        self.set_font("Roboto", "", 10)
        self.set_text_color(*DARK)
        ty = y + 14
        for line in lines:
            self.set_xy(x + 4, ty)
            self.multi_cell(w - 8, 5, line)
            ty = self.get_y() + 1


def build():
    pdf = Deck()

    pdf.add_page()
    pdf.n = 1
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, 297, 210, "F")
    pdf.set_fill_color(*TEAL)
    pdf.rect(0, 0, 8, 210, "F")
    pdf.set_fill_color(*ACCENT)
    pdf.rect(8, 178, 289, 4, "F")
    pdf.set_font("Roboto", "", 12)
    pdf.set_text_color(180, 200, 210)
    pdf.set_xy(24, 36)
    pdf.cell(0, 8, "PRE-SEED  ·  FLIGHT MONITORING  ·  TELEGRAM ALERTS")
    pdf.set_font("Roboto", "B", 48)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(24, 54)
    pdf.cell(0, 18, "Fly456")
    pdf.set_font("Roboto", "", 15)
    pdf.set_text_color(200, 220, 225)
    pdf.set_xy(24, 78)
    pdf.multi_cell(
        250,
        7,
        "You set origin, destination, dates and max price.\nWe monitor flights and notify you on Telegram - so you can book fast.",
    )
    pdf.set_font("Roboto", "B", 13)
    pdf.set_text_color(*ACCENT)
    pdf.set_xy(24, 110)
    pdf.cell(0, 7, "Two products: Economy cabin  ·  Business cabin")
    pdf.set_font("Roboto", "", 12)
    pdf.set_text_color(160, 180, 190)
    pdf.set_xy(24, 130)
    pdf.cell(0, 6, "Asking: ~150k EUR pre-seed  ·  fly456.com  ·  @fly456bot")
    pdf.set_xy(24, 145)
    pdf.cell(0, 6, "Emiliano Tichauer  ·  Founder")
    pdf.set_xy(24, 190)
    pdf.cell(0, 5, "1/6")

    y = pdf.slide("Problem", "Good fares disappear before travelers can act")
    pdf.bullets(
        y,
        [
            "Flight prices move in hours. Checking sites manually is slow and easy to miss.",
            "Generic deal feeds are noisy - they are not your route, dates or budget.",
            "By the time you see a fare, seats and price are often already gone.",
        ],
    )

    y = pdf.slide("Solution", "Named monitoring + Telegram alert to book fast")
    pdf.box(14, y, 88, 85, "You define the flight", ["Origin", "Destination", "Dates", "Maximum price", "", "Fly456 watches that exact brief."])
    pdf.box(108, y, 88, 85, "We notify on Telegram", ["Alert in your Telegram inbox", "via @fly456bot", "Built to help you reserve fast", "before the fare moves again", "", "We do not sell tickets."])
    pdf.box(202, y, 80, 85, "Two cabin products", ["Economy - economy cabin", "Business - business cabin", "", "Same alert logic,", "different cabin."])

    y = pdf.slide("Product", "Economy and Business - same monitoring, different cabin")
    pdf.box(
        14,
        y,
        130,
        90,
        "Fly456 Economy",
        [
            "Monitors economy-cabin opportunities",
            "Alert = origin + destination + dates + max price",
            "Telegram notification when a match appears",
            "For leisure / price-sensitive travelers",
        ],
    )
    pdf.box(
        152,
        y,
        130,
        90,
        "Fly456 Business",
        [
            "Monitors business-cabin opportunities",
            "Same named criteria, business fares",
            "Telegram notification to book fast",
            "For premium-cabin travelers waiting",
            "for the right price window",
        ],
    )

    y = pdf.slide("Traction & model", "Replace brackets with live numbers before sending")
    pdf.box(
        14,
        y,
        130,
        90,
        "Traction",
        [
            "Product live: fly456.com + @fly456bot",
            "[N] active route alerts monitored",
            "[P] paying subscribers · EUR [A] MRR",
            "Stripe checkout inside Telegram",
        ],
    )
    pdf.box(
        152,
        y,
        130,
        90,
        "Model & ask (~150k EUR)",
        [
            "Subscription for named route alerts",
            "Economy + Business cabin products",
            "Later: affiliate / partner take-rate",
            "Funds: better monitoring, faster alerts,",
            "convert and retain paying users",
        ],
    )

    y = pdf.slide("Team", "Operator-builder shipping the full loop")
    pdf.bullets(
        y,
        [
            "Emiliano Tichauer - Founder",
            "Built Parvus Media since 2013 (AdTech, data, performance products)",
            "Owns the loop end-to-end: flight monitoring, Telegram UX, Stripe billing",
            "Contact: [email]  ·  LinkedIn: linkedin.com/in/etichauer  ·  fly456.com",
        ],
    )

    for path in (OUT, OUT_ROOT, OUT_ART):
        path.parent.mkdir(parents=True, exist_ok=True)
        pdf.output(path)
        print(f"Wrote {path}")


if __name__ == "__main__":
    build()

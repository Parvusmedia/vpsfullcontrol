#!/usr/bin/env python3
"""Short Fly456 one-pager / micro-deck for Kima-style cold outreach."""

from pathlib import Path

from fpdf import FPDF

OUT = Path(__file__).resolve().parent / "Fly456_Kima_OnePager.pdf"
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
        self.set_font("Roboto", "B", 24)
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

    # 1 Cover
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
    pdf.set_xy(24, 40)
    pdf.cell(0, 8, "PRE-SEED  ·  CONSUMER TRAVEL  ·  TELEGRAM-NATIVE")
    pdf.set_font("Roboto", "B", 48)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(24, 58)
    pdf.cell(0, 18, "Fly456")
    pdf.set_font("Roboto", "", 16)
    pdf.set_text_color(200, 220, 225)
    pdf.set_xy(24, 82)
    pdf.multi_cell(250, 8, "Cheap-flight opportunities EU/US to LatAm.\nFree Telegram channels + paid route alerts.")
    pdf.set_font("Roboto", "B", 12)
    pdf.set_text_color(*ACCENT)
    pdf.set_xy(24, 120)
    pdf.cell(0, 7, "Asking: ~150k EUR pre-seed  ·  fly456.com")
    pdf.set_font("Roboto", "", 11)
    pdf.set_text_color(160, 180, 190)
    pdf.set_xy(24, 150)
    pdf.cell(0, 6, "Emiliano Tichauer  ·  Founder  ·  Parvus Media / Fly456")
    pdf.set_xy(24, 190)
    pdf.cell(0, 5, "1/6")

    # 2 Problem
    y = pdf.slide("Problem", "Good fares to LatAm disappear before people see them")
    pdf.bullets(
        y,
        [
            "Diaspora and leisure travelers watch dozens of groups and still miss deals.",
            "Airline and OTA prices move in hours; generic alerts are noisy.",
            "Existing flight clubs are crowded, slow, or not focused on LatAm corridors.",
        ],
    )

    # 3 Solution
    y = pdf.slide("Solution", "Detect opportunities. Alert fast. Stay on Telegram.")
    pdf.box(14, y, 88, 70, "Free", ["Public Telegram channels", "by origin/destination", "EU/US to LatAm routes", "Discovery engine"])
    pdf.box(108, y, 88, 70, "Premium", ["Personal route alerts", "Origin + dest + dates", "Max price threshold", "Inbox via @fly456bot"])
    pdf.box(202, y, 80, 70, "Not us", ["We do not sell tickets", "User books with airline/OTA", "We win on alerts + later", "affiliate / data upside"])

    # 4 Traction placeholders
    y = pdf.slide("Traction", "Replace brackets with live numbers before sending")
    pdf.bullets(
        y,
        [
            "[N] free channels live on Telegram",
            "[M] members across channels (unique approx. [U])",
            "[P] paying Premium subscribers  ·  [EUR] MRR",
            "Plans from ~1 EUR/alert/mo  ·  Stripe checkout in Telegram",
            "Product live: fly456.com + @fly456bot",
        ],
    )

    # 5 Model + ask
    y = pdf.slide("Model & ask", "Subscription now. Affiliate / data later.")
    pdf.box(
        14,
        y,
        130,
        85,
        "Business model",
        [
            "Now: Premium route alerts (SaaS-lite)",
            "Next: affiliate / partner take-rate",
            "Later: demand signals for OTAs",
            "GTM: organic Telegram + SEO routes",
            "Cost base: detection + messaging infra",
        ],
    )
    pdf.box(
        152,
        y,
        130,
        85,
        "The ask (~150k EUR)",
        [
            "Scale high-intent LatAm corridors",
            "Sharper detection + faster alerts",
            "Conversion free to Premium",
            "Pilot affiliate monetization",
            "Keep burn low; prove LTV/CAC",
        ],
    )

    # 6 Team
    y = pdf.slide("Team", "Operator-builder with AdTech & product DNA")
    pdf.bullets(
        y,
        [
            "Emiliano Tichauer — Founder (Spain; LatAm roots)",
            "Built Parvus Media since 2013 (AdTech, data, performance; Madrid + Dubai footprint)",
            "Ships products end-to-end: detection, Telegram UX, Stripe billing",
            "Contact: [email]  ·  LinkedIn: linkedin.com/in/etichauer  ·  fly456.com",
        ],
    )

    pdf.output(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()

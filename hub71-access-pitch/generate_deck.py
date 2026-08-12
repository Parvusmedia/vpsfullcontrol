#!/usr/bin/env python3
"""Generate Hub71 Access Programme pitch deck PDF for NextConvers.

Required sections (Hub71):
  Problem, solution/value proposition, business model, competition,
  market, traction, founding team, previous and next fundraising,
  plans for Hub71 and Abu Dhabi.
"""

from pathlib import Path

from fpdf import FPDF

OUT = Path(__file__).resolve().parent / "NextConvers_Hub71_Access_Pitch.pdf"
FONT_REG = "/tmp/Roboto-Regular.ttf"
FONT_BOLD = "/tmp/Roboto-Bold.ttf"

NAVY = (12, 35, 48)
TEAL = (0, 120, 120)
ACCENT = (232, 145, 58)
LIGHT = (245, 248, 250)
MUTED = (90, 110, 120)
WHITE = (255, 255, 255)
DARK = (22, 32, 40)


class Deck(FPDF):
    def __init__(self):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.set_auto_page_break(auto=False)
        self.add_font("Roboto", "", FONT_REG)
        self.add_font("Roboto", "B", FONT_BOLD)
        self.slide_no = 0
        self.total_slides = 11

    def new_slide(self, eyebrow: str = "", title: str = ""):
        self.add_page()
        self.slide_no += 1
        self.set_fill_color(*TEAL)
        self.rect(0, 0, 6, 210, "F")
        self.set_fill_color(*LIGHT)
        self.rect(6, 0, 291, 14, "F")
        self.set_font("Roboto", "", 9)
        self.set_text_color(*MUTED)
        self.set_xy(14, 4)
        self.cell(200, 6, "NextConvers  ·  Hub71 Access Programme  ·  Cohort 20", align="L")
        self.set_xy(230, 4)
        self.cell(50, 6, f"{self.slide_no} / {self.total_slides}", align="R")
        y = 22
        if eyebrow:
            self.set_font("Roboto", "B", 10)
            self.set_text_color(*TEAL)
            self.set_xy(14, y)
            self.cell(0, 6, eyebrow.upper())
            y += 8
        if title:
            self.set_font("Roboto", "B", 24)
            self.set_text_color(*NAVY)
            self.set_xy(14, y)
            self.multi_cell(270, 9, title)
            y = self.get_y() + 4
        return y

    def footer_note(self, text: str):
        self.set_font("Roboto", "", 8)
        self.set_text_color(*MUTED)
        self.set_xy(14, 198)
        self.cell(270, 5, text)

    def section_box(self, x, y, w, h, title, body_lines, fill=LIGHT):
        self.set_fill_color(*fill)
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
        for line in body_lines:
            self.set_xy(x + 4, ty)
            self.multi_cell(w - 8, 5, line)
            ty = self.get_y() + 1
        return ty

    def bullet(self, x, y, text, width=270):
        self.set_font("Roboto", "", 11)
        self.set_text_color(*DARK)
        self.set_xy(x, y)
        self.cell(5, 6, "-")
        self.set_xy(x + 5, y)
        self.multi_cell(width - 5, 6, text)
        return self.get_y() + 1

    def metric(self, x, y, value, label):
        self.set_font("Roboto", "B", 28)
        self.set_text_color(*TEAL)
        self.set_xy(x, y)
        self.cell(60, 12, value, align="C")
        self.set_font("Roboto", "", 10)
        self.set_text_color(*MUTED)
        self.set_xy(x, y + 12)
        self.multi_cell(60, 5, label, align="C")


def build():
    pdf = Deck()

    # ── 1. Cover + agenda matching Hub71 checklist ────────────
    pdf.add_page()
    pdf.slide_no = 1
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, 297, 210, "F")
    pdf.set_fill_color(*TEAL)
    pdf.rect(0, 0, 8, 210, "F")
    pdf.set_fill_color(*ACCENT)
    pdf.rect(8, 180, 289, 4, "F")

    pdf.set_font("Roboto", "", 12)
    pdf.set_text_color(180, 200, 210)
    pdf.set_xy(24, 28)
    pdf.cell(0, 8, "HUB71 ACCESS PROGRAMME  ·  COHORT 20  ·  APPLICATION PITCH")

    pdf.set_font("Roboto", "B", 44)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(24, 44)
    pdf.cell(0, 16, "NextConvers")

    pdf.set_font("Roboto", "", 16)
    pdf.set_text_color(200, 220, 225)
    pdf.set_xy(24, 64)
    pdf.multi_cell(240, 8, "AI B2B lead scoring & prospecting before outreach begins.")

    pdf.set_font("Roboto", "B", 11)
    pdf.set_text_color(*ACCENT)
    pdf.set_xy(24, 90)
    pdf.cell(0, 6, "This deck covers every Hub71 required point:")

    agenda = [
        "1. Problem",
        "2. Solution / value proposition",
        "3. Business model",
        "4. Competition",
        "5. Market",
        "6. Traction",
        "7. Founding team",
        "8. Previous and next fundraising",
        "9. Plans for Hub71 and Abu Dhabi",
    ]
    pdf.set_font("Roboto", "", 11)
    pdf.set_text_color(200, 220, 225)
    left = agenda[:5]
    right = agenda[5:]
    y0 = 100
    for i, item in enumerate(left):
        pdf.set_xy(24, y0 + i * 7)
        pdf.cell(120, 6, item)
    for i, item in enumerate(right):
        pdf.set_xy(160, y0 + i * 7)
        pdf.cell(120, 6, item)

    pdf.set_font("Roboto", "B", 11)
    pdf.set_text_color(*ACCENT)
    pdf.set_xy(24, 155)
    pdf.cell(0, 6, "Confidential  ·  nextconvers.com  ·  Parvus Media S.L.U.")

    pdf.set_font("Roboto", "", 10)
    pdf.set_text_color(140, 165, 175)
    pdf.set_xy(24, 190)
    pdf.cell(0, 5, "1 / 11")

    # ── 2. Problem ────────────────────────────────────────────
    y = pdf.new_slide("1. Problem", "Sales teams waste outreach on the wrong people")
    y = pdf.bullet(14, y, "B2B outbound volume is rising, but reply and acceptance rates keep falling.")
    y = pdf.bullet(14, y, "CRMs and sequencers move leads - they do not decide who deserves attention first.")
    y = pdf.bullet(14, y, "Teams scrape lists, buy contacts, and spray messages without ICP affinity scoring.")
    y = pdf.bullet(14, y, "Result: burned domains, wasted SDRs, and pipeline full of low-fit noise.")
    y += 6
    pdf.section_box(
        14,
        y,
        268,
        52,
        "The gap in the stack",
        [
            "Outreach tools send. CRMs store. Ads generate form fills.",
            "Almost nothing decides - before first contact - who is actually worth a conversation.",
            "That missing decision layer is where NextConvers sits.",
        ],
    )
    pdf.footer_note("Required: Problem")

    # ── 3. Solution / value proposition ───────────────────────
    y = pdf.new_slide(
        "2. Solution / value proposition",
        "AI decision layer before outreach - more conversations with buyers",
    )
    y = pdf.bullet(14, y, "Solution: identify and prioritize B2B prospects by role, seniority, company, industry and geo fit.")
    y = pdf.bullet(14, y, "Each profile gets a clear 1-5 star affinity score: who to contact, in what order, before outreach.")
    y = pdf.bullet(14, y, "Sync scored leads via webhooks into CRM and outreach tools - no change to existing workflows.")
    y = pdf.bullet(14, y, "We do not send messages. We make outreach smarter before it starts.")
    y += 3
    pdf.metric(20, y, "+40%", "Expected acceptance\nrate lift")
    pdf.metric(90, y, "+25%", "More qualified\nopportunities")
    pdf.metric(160, y, "+20%", "Sales conversion\nimprovement")
    pdf.metric(230, y, "-30%", "Less wasted sales\nteam effort")
    y += 36
    pdf.section_box(
        14,
        y,
        268,
        36,
        "Value proposition",
        [
            "NextConvers is the step before outreach: plug-and-play ICP scoring for sales, growth and agencies,",
            "feeding tools they already pay for (CRM, sequencers) so teams talk to people who can actually buy.",
        ],
    )
    pdf.footer_note("Required: Solution / value proposition  |  Impact figures from nextconvers.com - replace with measured results when available.")

    # ── 4. Business model ─────────────────────────────────────
    y = pdf.new_slide("3. Business model", "SaaS usage + seats, expandable into MENA enterprise")
    y = pdf.bullet(14, y, "Core: subscription / usage-based SaaS for scored prospects delivered into the sales stack.")
    y = pdf.bullet(14, y, "Expansion: agency plans, multi-account workspaces, higher-volume ICP scoring.")
    y = pdf.bullet(14, y, "Upsell path: PLG reports (DataForMedia) to enterprise decision layer (NextConvers).")
    y = pdf.bullet(14, y, "GTM: product-led entry + demos for mid-market / enterprise sales orgs.")
    y += 6
    pdf.section_box(
        14,
        y,
        130,
        55,
        "Revenue logic",
        [
            "Recurring SaaS (seats / volume).",
            "Land with one team, then expand org-wide.",
            "Low implementation cost, fast sales cycle.",
            "High switching cost once embedded in CRM.",
        ],
    )
    pdf.section_box(
        152,
        y,
        130,
        55,
        "Unit economics focus",
        [
            "Gross margin typical of AI SaaS.",
            "CAC via outbound + partners + PLG.",
            "Payback driven by SDR productivity.",
            "MENA enterprise ACV upside via Hub71.",
        ],
    )
    pdf.footer_note("Required: Business model  |  Insert exact pricing / ACV before final submit if available.")

    # ── 5. Competition ────────────────────────────────────────
    y = pdf.new_slide("4. Competition", "We sit before outreach - not instead of it")
    headers = ["", "NextConvers", "Enrichment\n(Apollo/ZoomInfo)", "Sequencers\n(Smartlead etc.)", "CRM"]
    col_w = [48, 52, 55, 55, 52]
    x0 = 14
    pdf.set_fill_color(*NAVY)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Roboto", "B", 9)
    x = x0
    for i, h in enumerate(headers):
        pdf.rect(x, y, col_w[i], 16, "F")
        pdf.set_xy(x + 1, y + 2)
        pdf.multi_cell(col_w[i] - 2, 5, h, align="C")
        x += col_w[i]
    rows = [
        ("Scores who to contact first", "Yes", "Partial", "No", "No"),
        ("Sends messages", "No", "No / limited", "Yes", "No"),
        ("Feeds existing stack", "Yes", "Export", "Native", "System of record"),
        ("ICP affinity 1-5 stars", "Core", "Filters", "No", "Custom fields"),
        ("Time-to-value", "Minutes", "Days", "Days", "Weeks"),
    ]
    yy = y + 16
    for ri, row in enumerate(rows):
        fill = LIGHT if ri % 2 == 0 else WHITE
        pdf.set_fill_color(*fill)
        x = x0
        for i, cell in enumerate(row):
            pdf.rect(x, yy, col_w[i], 10, "F")
            pdf.set_text_color(*TEAL if i == 1 else DARK)
            pdf.set_font("Roboto", "B" if i in (0, 1) else "", 9)
            pdf.set_xy(x + 1, yy + 2.5)
            pdf.cell(col_w[i] - 2, 5, cell, align="C" if i else "L")
            x += col_w[i]
        yy += 10
    pdf.set_xy(14, yy + 6)
    pdf.set_font("Roboto", "", 10)
    pdf.set_text_color(*DARK)
    pdf.multi_cell(
        270,
        5,
        "Moat: decision layer + workflow lock-in via sync + scoring tuned on conversion feedback (not only static firmographics).",
    )
    pdf.footer_note("Required: Competition")

    # ── 6. Market ─────────────────────────────────────────────
    y = pdf.new_slide("5. Market", "Sales intelligence in a large, expanding B2B stack")
    y = pdf.bullet(14, y, "TAM: global sales engagement + revenue intelligence software (multi-billion USD category).")
    y = pdf.bullet(14, y, "SAM: mid-market & enterprise B2B teams that already buy CRM + sequencers + enrichment.")
    y = pdf.bullet(14, y, "SOM (near-term): EU outbound teams + GCC expansion with Abu Dhabi as regional HQ.")
    y = pdf.bullet(14, y, "Why now: AI scoring becomes table stakes; buyers reject spray-and-pray; professional signals are richer.")
    y += 6
    pdf.section_box(
        14,
        y,
        268,
        48,
        "Why Abu Dhabi / GCC matters",
        [
            "High-ticket B2B sales across banking, telecom, energy, government and holding groups.",
            "Hub71 partners (banks, etisalat/e&, Microsoft, AWS, VCs) are natural design partners and buyers.",
            "Parvus Media already has a Dubai footprint - Abu Dhabi becomes the scale HQ for NextConvers.",
        ],
    )
    pdf.footer_note("Required: Market")

    # ── 7. Traction ───────────────────────────────────────────
    y = pdf.new_slide("6. Traction", "Product live · early commercial · domain proof")
    pdf.section_box(
        14,
        y,
        130,
        100,
        "Product & GTM traction",
        [
            "- Live product at nextconvers.com",
            "- Clear ICP: B2B sales, growth, agencies",
            "- Integrations path: CRM + outreach webhooks",
            "- Adjacent PLG wedge live: DataForMedia",
            "  (LinkedIn audience intelligence)",
            "- Demo-led motion for enterprise teams",
            "",
            "BEFORE SUBMIT - replace with:",
            "paying logos · MRR/ARR · pilots · waitlist",
        ],
    )
    pdf.section_box(
        152,
        y,
        130,
        100,
        "Operating proof behind the product",
        [
            "- Parvus Media since 2013 (AdTech,",
            "  data, performance)",
            "- Clients across Europe, LatAm, Middle East",
            "- Offices: Madrid & Dubai footprint",
            "- Same team DNA: signals -> decisions",
            "  for commercial teams",
            "",
            "Traction thesis: AdTech operators",
            "shipping an AI sales-intelligence SaaS,",
            "not a slide-only startup.",
        ],
    )
    pdf.footer_note("Required: Traction  |  Update logos / revenue before submission.")

    # ── 8. Founding team ──────────────────────────────────────
    y = pdf.new_slide("7. Founding team", "Operator-builders with AdTech & B2B data DNA")
    pdf.section_box(
        14,
        y,
        268,
        105,
        "Emiliano Tichauer - Founder & Product Lead, NextConvers",
        [
            "- Founder & Product Lead at NextConvers",
            "- Partner / advisor at Parvus Media (AdTech & performance products since 2013)",
            "- 20+ years building media, data and commercial products across Europe, LatAm and Middle East",
            "- Prior ventures: Wolly (local biz SEO), CULSION, Culturalia European Hispanics",
            "- Based Madrid; Parvus Media footprint includes Madrid & Dubai",
            "- Commitment: at least one founder relocates long-term to Abu Dhabi and builds the local team",
            "",
            "Abu Dhabi hiring plan (year 1): commercial lead (GCC) + AI/engineering hire + Hub71 partner GTM.",
            "BEFORE SUBMIT: add co-founders / key hires with LinkedIn if available.",
        ],
    )
    pdf.footer_note("Required: Founding team")

    # ── 9. Previous and next fundraising ──────────────────────
    y = pdf.new_slide("8. Previous and next fundraising", "Bootstrapped to date · Hub71 SAFE now · seed after")
    pdf.section_box(
        14,
        y,
        88,
        110,
        "Previous fundraising",
        [
            "- No institutional round yet",
            "- Bootstrapped / founder-funded",
            "- Product built without VC",
            "- Parvus Media ops funded",
            "  early R&D and GTM learning",
            "",
            "Status: pre-seed / Access-stage",
            "company seeking first structured",
            "capital via Hub71 SAFE.",
        ],
    )
    pdf.section_box(
        108,
        y,
        88,
        110,
        "This round (Hub71 Access)",
        [
            "- AED 250,000 cash via SAFE",
            "- AED 250,000 in-kind incentives",
            "- Optional top-up +AED 250,000",
            "  for equity after strong year",
            "",
            "Use of funds (12 months):",
            "- Founder relocate + AD team",
            "- MENA corporate pilots",
            "- AI scoring depth",
            "- ADGM / visas / ops",
        ],
    )
    pdf.section_box(
        202,
        y,
        80,
        110,
        "Next fundraising",
        [
            "- Target: seed / pre-A",
            "  after Access + Demo Day",
            "- Timing: ~12 months",
            "  (post Hub71 KPIs)",
            "- Investors to engage:",
            "  MEVP, Shorooq,",
            "  Global Ventures,",
            "  UAE Angels, Hub71",
            "  capital partners",
            "- Goal: scale MENA + EU",
            "  GTM with proven lift",
        ],
    )
    pdf.footer_note("Required: Previous and next fundraising")

    # ── 10. Plans for Hub71 and Abu Dhabi ─────────────────────
    y = pdf.new_slide("9. Plans for Hub71 and Abu Dhabi", "Abu Dhabi as MENA HQ for AI sales intelligence")
    y = pdf.bullet(14, y, "Relocate at least one founder long-term to Abu Dhabi and hire locally within year one.")
    y = pdf.bullet(14, y, "Operate via ADGM-friendly setup using Hub71 licensing, visa, housing and office support.")
    y = pdf.bullet(14, y, "Run 3-5 corporate / agency pilots with Hub71 market partners (banks, telco, enterprise SaaS).")
    y = pdf.bullet(14, y, "Complete the Techstars-powered guided track; prepare fundraising showcase and Demo Day.")
    y = pdf.bullet(14, y, "Use Hub71 capital network for the next (seed / pre-A) round after proving MENA traction.")
    y += 4
    pdf.section_box(
        14,
        y,
        130,
        48,
        "12-month KPIs (draft)",
        [
            "- Live AD entity + local team nucleus",
            "- >=3 paid MENA design partners",
            "- Scoring / reply-rate lift proven",
            "- Pipeline to seed / pre-A after Demo Day",
        ],
    )
    pdf.section_box(
        152,
        y,
        130,
        48,
        "Why Hub71 specifically",
        [
            "- Sector-agnostic Access + AI narrative",
            "- Corporate distribution into GCC buyers",
            "- SAFE + in-kind de-risks market entry",
            "- Dubai presence to Abu Dhabi scale HQ",
        ],
    )
    pdf.footer_note("Required: Plans for Hub71 and Abu Dhabi")

    # ── 11. Closing ask ───────────────────────────────────────
    y = pdf.new_slide("Closing ask", "Join Hub71 Access - scale NextConvers from Abu Dhabi")
    pdf.section_box(
        14,
        y,
        268,
        72,
        "We are applying for",
        [
            "Hub71 Access Programme (Cohort 20) - 12 months starting February 2027.",
            "Package: AED 250,000 cash via SAFE + AED 250,000 flexible in-kind incentives.",
            "Commitment: founder relocation long-term + building the NextConvers team out of Abu Dhabi.",
            "Ambition: become the default AI decision layer before outreach for B2B teams across MENA & beyond.",
        ],
    )
    pdf.set_font("Roboto", "B", 14)
    pdf.set_text_color(*NAVY)
    pdf.set_xy(14, y + 88)
    pdf.cell(0, 8, "Checklist covered: Problem · Solution/VP · Business model · Competition · Market · Traction · Team · Fundraising · Hub71/Abu Dhabi")
    pdf.set_font("Roboto", "B", 12)
    pdf.set_xy(14, y + 102)
    pdf.cell(0, 6, "nextconvers.com   ·   Contact: Emiliano Tichauer")
    pdf.set_font("Roboto", "", 10)
    pdf.set_text_color(*MUTED)
    pdf.set_xy(14, y + 112)
    pdf.cell(0, 5, "Parvus Media S.L.U.  ·  Madrid  ·  Dubai footprint  ·  Expanding to Abu Dhabi via Hub71")
    pdf.footer_note("Application deadline Cohort 20: 21 August 2026")

    pdf.output(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()

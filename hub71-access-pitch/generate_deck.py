#!/usr/bin/env python3
"""Generate Hub71 Access Programme pitch deck PDF for NextConvers."""

from pathlib import Path

from fpdf import FPDF

OUT = Path(__file__).resolve().parent / "NextConvers_Hub71_Access_Pitch.pdf"
FONT_REG = "/tmp/Roboto-Regular.ttf"
FONT_BOLD = "/tmp/Roboto-Bold.ttf"

# Brand palette (avoid purple/cream AI clichés; Hub71-friendly deep teal + sand)
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
        self.total_slides = 12

    def new_slide(self, eyebrow: str = "", title: str = ""):
        self.add_page()
        self.slide_no += 1
        # Left accent bar
        self.set_fill_color(*TEAL)
        self.rect(0, 0, 6, 210, "F")
        # Top thin line
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
            self.set_font("Roboto", "B", 26)
            self.set_text_color(*NAVY)
            self.set_xy(14, y)
            self.multi_cell(270, 10, title)
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
        self.cell(5, 6, "•")
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

    # ── 1. Cover ──────────────────────────────────────────────
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
    pdf.set_xy(24, 40)
    pdf.cell(0, 8, "HUB71 ACCESS PROGRAMME  ·  COHORT 20  ·  APPLICATION PITCH")

    pdf.set_font("Roboto", "B", 48)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(24, 60)
    pdf.cell(0, 18, "NextConvers")

    pdf.set_font("Roboto", "", 18)
    pdf.set_text_color(200, 220, 225)
    pdf.set_xy(24, 82)
    pdf.multi_cell(240, 9, "AI B2B lead scoring & prospecting\nbefore outreach begins.")

    pdf.set_font("Roboto", "", 12)
    pdf.set_text_color(160, 185, 195)
    pdf.set_xy(24, 120)
    pdf.multi_cell(
        240,
        7,
        "We identify the right people, score them 1-5 by ICP fit,\nand sync prioritized prospects into CRM & outreach tools.",
    )

    pdf.set_font("Roboto", "B", 11)
    pdf.set_text_color(*ACCENT)
    pdf.set_xy(24, 155)
    pdf.cell(0, 6, "Confidential  ·  nextconvers.com  ·  Parvus Media S.L.U.")

    pdf.set_font("Roboto", "", 10)
    pdf.set_text_color(140, 165, 175)
    pdf.set_xy(24, 190)
    pdf.cell(0, 5, "1 / 12")

    # ── 2. Problem ────────────────────────────────────────────
    y = pdf.new_slide("Problem", "Sales teams waste outreach on the wrong people")
    y = pdf.bullet(14, y, "B2B outbound volume is rising, but reply and acceptance rates keep falling.")
    y = pdf.bullet(14, y, "CRMs and sequencers move leads — they do not decide who deserves attention first.")
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
            "Almost nothing decides — before first contact — who is actually worth a conversation.",
            "That missing decision layer is where NextConvers sits.",
        ],
    )
    pdf.footer_note("Hub71 required section: Problem")

    # ── 3. Solution ───────────────────────────────────────────
    y = pdf.new_slide("Solution", "The decision layer before outreach")
    y = pdf.bullet(14, y, "NextConvers finds and prioritizes B2B prospects using role, seniority, company, industry and geo fit.")
    y = pdf.bullet(14, y, "Each profile gets a clear 1-5 star affinity score so teams know who to contact, in what order.")
    y = pdf.bullet(14, y, "Scored leads sync via webhooks into CRM and outreach tools — no change to existing workflows.")
    y = pdf.bullet(14, y, "We do not send messages. We make outreach smarter before it starts.")
    y += 4
    w = 85
    pdf.section_box(14, y, w, 55, "01  Identify", ["Source people who match", "the ICP from professional", "and engagement signals."], LIGHT)
    pdf.section_box(14 + w + 6, y, w, 55, "02  Score", ["Rank affinity 1-5 stars by role,", "experience, company size,", "industry and geo."], LIGHT)
    pdf.section_box(14 + 2 * (w + 6), y, w, 55, "03  Sync", ["Push prioritized leads into", "CRM / sequencers daily so", "SDRs work the best first."], LIGHT)
    pdf.footer_note("Hub71 required section: Solution")

    # ── 4. Value proposition ──────────────────────────────────
    y = pdf.new_slide("Value proposition", "More conversations with people who can buy")
    pdf.metric(20, y, "+40%", "Expected acceptance\nrate lift")
    pdf.metric(90, y, "+25%", "More qualified\nopportunities")
    pdf.metric(160, y, "+20%", "Sales conversion\nimprovement")
    pdf.metric(230, y, "-30%", "Less wasted sales\nteam effort")
    y += 42
    pdf.section_box(
        14,
        y,
        268,
        58,
        "Who wins",
        [
            "B2B sales & SDR teams · Growth / RevOps · Founders doing outbound · Agencies running prospecting at scale.",
            "Plug & play: minutes to start, not weeks. Flexible SaaS — pay for usage, no long lock-in.",
            "Positioning: “NextConvers is the step before outreach.” We fuel tools teams already pay for.",
        ],
    )
    pdf.footer_note("Impact figures from product positioning (nextconvers.com) — replace with measured customer results when available.")

    # ── 5. Product ────────────────────────────────────────────
    y = pdf.new_slide("Product", "AI scoring that sales teams actually use")
    cols = [
        (14, "Affinity engine", ["Role & seniority", "Company attributes", "Industry + geo fit", "1-5 star prioritization"]),
        (108, "Integrations", ["Webhooks to CRM", "Outreach sequencers", "CSV / API export", "Paid media audiences"]),
        (202, "Team UX", ["Minutes to onboard", "Shared team insights", "Agency multi-account", "No technical project"]),
    ]
    for x, title, lines in cols:
        pdf.section_box(x, y, 88, 78, title, lines)
    pdf.footer_note("Complementary wedge: DataForMedia (dataformedia.com) - LinkedIn audience intelligence reports feeding the same signal thesis.")

    # ── 6. Business model ─────────────────────────────────────
    y = pdf.new_slide("Business model", "SaaS usage + team seats, expandable into MENA enterprise")
    y = pdf.bullet(14, y, "Core: subscription / usage-based SaaS for scored prospects delivered into the sales stack.")
    y = pdf.bullet(14, y, "Expansion: agency plans, multi-account workspaces, higher volume ICP scoring.")
    y = pdf.bullet(14, y, "Upsell path: from PLG data reports (DataForMedia) to enterprise decision layer (NextConvers).")
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
    pdf.footer_note("Hub71 required section: Business model — insert exact pricing tiers / ACV before final submit if available.")

    # ── 7. Market ─────────────────────────────────────────────
    y = pdf.new_slide("Market", "Sales intelligence sits in a large, expanding B2B stack")
    y = pdf.bullet(14, y, "TAM: global sales engagement + revenue intelligence software (multi-billion USD category).")
    y = pdf.bullet(14, y, "SAM: mid-market & enterprise B2B teams that already buy CRM + sequencers + data enrichment.")
    y = pdf.bullet(14, y, "SOM (near-term): Spanish / EU outbound teams + GCC expansion via Abu Dhabi as regional HQ.")
    y = pdf.bullet(14, y, "Why now: AI scoring becomes table stakes; buyers reject spray-and-pray outbound; LinkedIn & professional signals are richer than ever.")
    y += 6
    pdf.section_box(
        14,
        y,
        268,
        48,
        "Why Abu Dhabi / GCC matters",
        [
            "High-ticket B2B sales culture across banking, telecom, energy, government and holding groups.",
            "Hub71 partners (banks, etisalat/e&, Microsoft, AWS, VCs) are natural design partners and buyers.",
            "Parvus Media already operates with a Dubai footprint — Abu Dhabi becomes the scale HQ for NextConvers.",
        ],
    )
    pdf.footer_note("Hub71 required section: Market")

    # ── 8. Competition ────────────────────────────────────────
    y = pdf.new_slide("Competition", "We sit before outreach — not instead of it")
    # Simple comparison table header
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
        "Moat thesis: decision layer + workflow lock-in via sync + proprietary scoring tuned on real conversion feedback loops (not just static firmographics).",
    )
    pdf.footer_note("Hub71 required section: Competition")

    # ── 9. Traction & funds ───────────────────────────────────
    y = pdf.new_slide("Traction & funds raised", "Product live · early commercial · bootstrapped")
    pdf.section_box(
        14,
        y,
        130,
        95,
        "Traction (current)",
        [
            "• Live product at nextconvers.com",
            "• Clear ICP: B2B sales, growth, agencies",
            "• Integrations path: CRM + outreach webhooks",
            "• Adjacent PLG wedge live: DataForMedia",
            "  (LinkedIn audience intelligence)",
            "• Domain proof via Parvus Media (since 2013)",
            "  — AdTech, data, performance, MENA clients",
            "",
            "BEFORE SUBMIT — replace with:",
            "paying logos · MRR/ARR · pilots · waitlist",
        ],
    )
    pdf.section_box(
        152,
        y,
        130,
        95,
        "Funds raised",
        [
            "• Bootstrapped to date (founder-funded)",
            "• Seeking Hub71 Access package:",
            "  AED 250k cash (SAFE) + AED 250k in-kind",
            "• Eligible top-up: +AED 250k for equity",
            "  after strong 12-month performance",
            "",
            "Use of funds (12 months):",
            "• MENA GTM + corporate pilots",
            "• Scoring / AI product depth",
            "• Founder + first Abu Dhabi hires",
            "• Compliance / ADGM setup support",
        ],
    )
    pdf.footer_note("Hub71 required section: Traction and funds raised — update numbers before PDF submission.")

    # ── 10. Team ──────────────────────────────────────────────
    y = pdf.new_slide("Founders / founding team", "Operator-builders with AdTech & B2B data DNA")
    pdf.section_box(
        14,
        y,
        268,
        100,
        "Emiliano Tichauer — Founder & Product Lead, NextConvers",
        [
            "• Founder & Product Lead at NextConvers",
            "• Partner / advisor at Parvus Media (AdTech & performance products since 2013)",
            "• 20+ years building media, data and commercial products across Europe, LatAm and Middle East",
            "• Prior ventures: Wolly (local biz SEO), CULSION, Culturalia European Hispanics",
            "• Based Madrid; Parvus Media footprint includes Madrid & Dubai — ready to commit a founder",
            "  long-term to Abu Dhabi to build the NextConvers team locally",
            "",
            "Team build plan in Abu Dhabi: commercial lead (GCC) + AI/engineering hire + shared GTM with Hub71 partners.",
            "BEFORE SUBMIT: add full-time co-founders / key hires with photos and LinkedIn if available.",
        ],
    )
    pdf.footer_note("Hub71 required section: Founders / Founding team")

    # ── 11. Plans for Hub71 & Abu Dhabi ────────────────────────
    y = pdf.new_slide("Plans for Hub71 & Abu Dhabi", "Abu Dhabi as MENA HQ for AI sales intelligence")
    y = pdf.bullet(14, y, "Relocate at least one founder long-term to Abu Dhabi and hire locally within the first programme year.")
    y = pdf.bullet(14, y, "Incorporate / operate via ADGM-friendly setup with Hub71 licensing & visa support.")
    y = pdf.bullet(14, y, "Run 3-5 corporate / agency pilots with Hub71 market partners (banks, telco, enterprise SaaS).")
    y = pdf.bullet(14, y, "Use Techstars-powered guided track for fundraising readiness and Demo Day.")
    y = pdf.bullet(14, y, "Connect with capital partners (MEVP, Shorooq, Global Ventures, UAE Angels, etc.) for post-SAFE round.")
    y += 4
    pdf.section_box(
        14,
        y,
        130,
        48,
        "12-month KPIs (draft)",
        [
            "• Live AD entity + local team nucleus",
            "• ≥3 paid MENA design partners",
            "• Scoring accuracy / reply-rate lift proven",
            "• Pipeline to seed / pre-A after Demo Day",
        ],
    )
    pdf.section_box(
        152,
        y,
        130,
        48,
        "Why Hub71 specifically",
        [
            "• Sector-agnostic Access + AI narrative",
            "• Corporate distribution into GCC buyers",
            "• SAFE + in-kind de-risks market entry",
            "• Dubai presence to Abu Dhabi scale HQ",
        ],
    )
    pdf.footer_note("Hub71 required section: Plans for Hub71 and Abu Dhabi")

    # ── 12. Ask / close ───────────────────────────────────────
    y = pdf.new_slide("The ask", "Join Hub71 Access — scale NextConvers from Abu Dhabi")
    pdf.section_box(
        14,
        y,
        268,
        70,
        "We are applying for",
        [
            "Hub71 Access Programme (Cohort 20) — 12 months starting February 2027.",
            "Package: AED 250,000 cash via SAFE + AED 250,000 flexible in-kind incentives.",
            "Commitment: founder relocation long-term + building the NextConvers team out of Abu Dhabi.",
            "Ambition: become the default AI decision layer before outreach for B2B teams across MENA & beyond.",
        ],
    )
    pdf.set_font("Roboto", "B", 16)
    pdf.set_text_color(*NAVY)
    pdf.set_xy(14, y + 85)
    pdf.cell(0, 8, "nextconvers.com   ·   Contact: Emiliano Tichauer")
    pdf.set_font("Roboto", "", 11)
    pdf.set_text_color(*MUTED)
    pdf.set_xy(14, y + 96)
    pdf.cell(0, 6, "Parvus Media S.L.U.  ·  Madrid  ·  Dubai footprint  ·  Expanding to Abu Dhabi via Hub71")
    pdf.footer_note("Application deadline Cohort 20: 21 August 2026")

    pdf.output(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()

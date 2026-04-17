import os
import re
from typing import Any, Dict, List

from fpdf import FPDF


REPORTS_DIR = "reports"

# Update if needed for your machine
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/Library/Fonts/Arial.ttf",
]


def resolve_font_path() -> str | None:
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def clean_text(text: Any) -> str:
    if text is None:
        return ""

    text = str(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2026": "...",
        "\u00a0": " ",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)

    return text


def safe_text(text: Any, max_len: int = 28) -> str:
    value = clean_text(text)
    if len(value) <= max_len:
        return value
    return value[: max_len - 3].rstrip() + "..."


class AuditPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(10, 10, 10)

        self.font_name = "Helvetica"
        font_path = resolve_font_path()

        if font_path:
            try:
                self.add_font("ArialUnicode", "", font_path)
                self.font_name = "ArialUnicode"
            except Exception:
                self.font_name = "Helvetica"

    def header(self):
        self.set_font(self.font_name, size=14)
        self.cell(0, 10, "1stkings AI Business Audit Report", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def section_title(self, title: str):
        self.ln(2)
        self.set_font(self.font_name, size=12)
        self.cell(0, 8, clean_text(title), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def section_body(self, text: Any):
        self.set_font(self.font_name, size=10)
        self.set_x(self.l_margin)
        safe_value = clean_text(text)

        if not safe_value:
            safe_value = "N/A"

        try:
            self.multi_cell(0, 6, safe_value)
        except Exception:
            fallback = safe_value.encode("latin-1", "ignore").decode("latin-1")
            if not fallback.strip():
                fallback = "Content could not be rendered."
            self.multi_cell(0, 6, fallback)

    def bullet_list(self, items: List[str]):
        self.set_font(self.font_name, size=10)

        if not items:
            self.section_body("N/A")
            return

        for item in items:
            bullet = f"- {clean_text(item)}"
            self.set_x(self.l_margin)
            try:
                self.multi_cell(0, 6, bullet)
            except Exception:
                fallback = bullet.encode("latin-1", "ignore").decode("latin-1")
                self.multi_cell(0, 6, fallback)

    def add_competitor_table(self, competitors: List[Dict[str, Any]]):
        self.set_font(self.font_name, size=9)

        if not competitors:
            self.section_body("No competitors available.")
            return

        col_widths = {
            "name": 42,
            "presence": 18,
            "engagement": 22,
            "automation": 20,
            "weighted_score": 24,
            "grade": 14,
        }

        headers = [
            ("name", "Name"),
            ("presence", "Pres."),
            ("engagement", "Eng."),
            ("automation", "Auto."),
            ("weighted_score", "Weighted"),
            ("grade", "Grade"),
        ]

        self.set_font(self.font_name, size=9)
        for key, label in headers:
            self.cell(col_widths[key], 8, label, border=1)
        self.ln()

        for comp in competitors:
            row = {
                "name": safe_text(comp.get("name", ""), 24),
                "presence": str(comp.get("presence", "")),
                "engagement": str(comp.get("engagement", "")),
                "automation": str(comp.get("automation", "")),
                "weighted_score": str(comp.get("weighted_score", "")),
                "grade": str(comp.get("grade", "")),
            }

            for key, _label in headers:
                cell_value = clean_text(row[key])
                try:
                    self.cell(col_widths[key], 8, cell_value, border=1)
                except Exception:
                    fallback = cell_value.encode("latin-1", "ignore").decode("latin-1")
                    self.cell(col_widths[key], 8, fallback, border=1)
            self.ln()


def generate_pdf_report(audit_id: int, audit_data: dict) -> str:
    os.makedirs(REPORTS_DIR, exist_ok=True)
    output_path = os.path.join(REPORTS_DIR, f"audit_{audit_id}.pdf")

    pdf = AuditPDF()
    pdf.add_page()

    target = audit_data.get("target_business", {})
    competitors = audit_data.get("competitors", [])
    insights = audit_data.get("insights", [])
    recommendations = audit_data.get("recommendations", [])
    market_summary = audit_data.get("market_summary", {})

    pdf.section_title("Business Overview")
    pdf.section_body(
        f"Business Name: {target.get('business_name', 'N/A')}\n"
        f"Website: {target.get('website', 'N/A')}\n"
        f"Industry: {target.get('industry', 'N/A')}\n"
        f"Summary: {target.get('summary', 'N/A')}\n"
        f"Core Offer: {target.get('core_offer', 'N/A')}"
    )

    pdf.section_title("Market Summary")
    pdf.section_body(
        f"Average Weighted Score: {market_summary.get('average_score', 0)}\n"
        f"Top Competitor Score: {market_summary.get('top_score', 0)}\n"
        f"Average Market Grade: {market_summary.get('average_grade', 'N/A')}"
    )

    pdf.section_title("Competitor Scores")
    pdf.add_competitor_table(competitors)

    pdf.section_title("Insights")
    pdf.bullet_list(insights)

    pdf.section_title("Recommendations")
    pdf.bullet_list(recommendations)

    pdf.output(output_path)
    return output_path
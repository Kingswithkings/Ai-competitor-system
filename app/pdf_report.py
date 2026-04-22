import os
import re
from typing import Any, Dict, List

from fpdf import FPDF


REPORTS_DIR = "reports"

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
        safe_value = clean_text(text) or "N/A"

        try:
            self.multi_cell(0, 6, safe_value)
        except Exception:
            fallback = safe_value.encode("latin-1", "ignore").decode("latin-1")
            self.multi_cell(0, 6, fallback or "Content could not be rendered.")

    def bullet_list(self, items: List[str]):
        if not items:
            self.section_body("N/A")
            return

        for item in items:
            self.section_body(f"- {item}")

    def add_competitor_table(self, competitors: List[Dict[str, Any]]):
        if not competitors:
            self.section_body("No competitors available.")
            return

        self.set_font(self.font_name, size=9)

        widths = {
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

        for key, label in headers:
            self.cell(widths[key], 8, label, border=1)
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

            for key, _ in headers:
                self.cell(widths[key], 8, clean_text(row[key]), border=1)
            self.ln()

    def add_ai_tools_section(self, ai_tools: List[Dict[str, Any]]):
        if not ai_tools:
            self.section_body("No AI tool recommendations available.")
            return

        for idx, item in enumerate(ai_tools, start=1):
            suggested_tools = item.get("suggested_tools", [])
            suggested_tools_str = ", ".join(suggested_tools) if isinstance(suggested_tools, list) else str(suggested_tools)

            block = (
                f"{idx}. Business Need: {item.get('business_need', 'N/A')}\n"
                f"Tool Category: {item.get('tool_category', 'N/A')}\n"
                f"Priority: {item.get('priority', 'N/A')}\n"
                f"Implementation Type: {item.get('implementation_type', 'N/A')}\n"
                f"Suggested Tools: {suggested_tools_str}\n"
                f"Reason: {item.get('reason', 'N/A')}"
            )
            self.section_body(block)
            self.ln(1)


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
    ai_tool_recommendations = audit_data.get("ai_tool_recommendations", [])

    pdf.section_title("Business Overview")
    pdf.section_body(
        f"Business Name: {target.get('business_name', 'N/A')}\n"
        f"Website: {target.get('website', 'N/A')}\n"
        f"Industry: {target.get('industry', 'N/A')}\n"
        f"Location: {target.get('location', 'N/A')}\n"
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

    pdf.section_title("Recommended AI Tools")
    pdf.add_ai_tools_section(ai_tool_recommendations)

    pdf.output(output_path)
    return output_path
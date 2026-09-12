"""Render the accompanying Markdown discussion proposal as a one-page PDF.

Requires reportlab and pypdf. This script produces no research results.
"""
from pathlib import Path
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "nhs_decision_brief.md"
OUTPUT = ROOT / "docs" / "nhs_decision_brief.pdf"


def inline(text):
    text = escape(text)
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" color="#005A75">\1</a>', text)
    return text


def build():
    navy = colors.HexColor("#17394E")
    body = ParagraphStyle("Body", fontName="Helvetica", fontSize=10.1,
                          leading=13.7, textColor=colors.HexColor("#233744"),
                          spaceAfter=7, alignment=TA_LEFT)
    title = ParagraphStyle("Title", parent=body, fontName="Helvetica-Bold",
                           fontSize=21, leading=24, textColor=navy, spaceAfter=11)
    subtitle = ParagraphStyle("Subtitle", parent=body, fontSize=9.1, leading=12.6,
                              textColor=navy, spaceAfter=11)
    section = ParagraphStyle("Section", parent=body, fontName="Helvetica-Bold",
                             fontSize=10, leading=13, spaceBefore=3, spaceAfter=7,
                             textColor=navy)
    foot = ParagraphStyle("Foot", parent=body, fontSize=7.9, leading=10.3,
                          textColor=colors.HexColor("#4B6572"), spaceAfter=0)
    blocks = re.split(r"\n\n|\n(?=\d\. \*\*)", SOURCE.read_text().strip())
    story = []
    for idx, block in enumerate(blocks):
        if block.startswith("# "):
            story.append(Paragraph(inline(block[2:]), title))
        elif idx == 1:
            story.append(Paragraph(inline(block.replace("  \n", "<br/>")).replace("&lt;br/&gt;", "<br/>"), subtitle))
        elif block.startswith("**Prospective"):
            story.append(Paragraph(inline(block), section))
        elif block.startswith("**Official basis:"):
            story.append(Spacer(1, 3))
            story.append(Paragraph(inline(block), foot))
        else:
            story.append(Paragraph(inline(block.replace("\n", " ")), body))
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=40,
                            leftMargin=40, topMargin=36, bottomMargin=34,
                            title="Where would extra listening change a decision?",
                            author="Shengwei Zhang", subject="NHS analyst discussion proposal")

    def decoration(canvas, document):
        canvas.setStrokeColor(colors.HexColor("#59A5AC"))
        canvas.setLineWidth(2)
        canvas.line(40, 24, A4[0] - 40, 24)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#4B6572"))
        canvas.drawString(40, 14, "Research discussion material | No field deployment or NHS endorsement")
        canvas.drawRightString(A4[0] - 40, 14, "1 / 1")

    doc.build(story, onFirstPage=decoration, onLaterPages=decoration)
    reader = PdfReader(OUTPUT)
    if len(reader.pages) != 1:
        raise RuntimeError(f"Expected one page, produced {len(reader.pages)}")
    extracted = reader.pages[0].extract_text()
    for required in ["Not co-designed", "universal", "BRFSS", "shadow mode", "NHS organisation"]:
        if required not in extracted:
            raise RuntimeError(f"Missing expected content: {required}")
    print(f"Verified one page and key content: {OUTPUT}")


if __name__ == "__main__":
    build()

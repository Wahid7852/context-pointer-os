from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


@dataclass
class Block:
    kind: str
    lines: list[str]


def escape_text(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    return text


def table_widths(rows: list[list[str]], max_width: float) -> list[float]:
    widths = []
    max_cols = max(len(r) for r in rows)
    for col in range(max_cols):
        longest = 0
        for row in rows:
            if col < len(row):
                longest = max(longest, len(row[col]))
        widths.append(max(1.0, min(26.0, longest * 0.09 + 0.35)))
    total = sum(widths)
    scale = max_width / total if total else 1.0
    return [w * scale for w in widths]


def parse_markdown_blocks(md_text: str) -> list[Block]:
    lines = md_text.splitlines()
    blocks: list[Block] = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            i += 1
            continue
        if line.startswith("```"):
            fence = line.strip()
            lang = fence[3:].strip()
            code: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i].rstrip("\n"))
                i += 1
            blocks.append(Block("code:" + lang, code))
            i += 1
            continue
        if line.startswith("|"):
            rows = [line]
            i += 1
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(lines[i].rstrip())
                i += 1
            blocks.append(Block("table", rows))
            continue
        if line.startswith("#"):
            blocks.append(Block("heading", [line]))
            i += 1
            continue
        if line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(lines[i][2:].strip())
                i += 1
            blocks.append(Block("list", items))
            continue
        para = [line]
        i += 1
        while i < len(lines):
            nxt = lines[i].rstrip()
            if not nxt or nxt.startswith("#") or nxt.startswith("```") or nxt.startswith("|") or nxt.startswith("- "):
                break
            para.append(nxt)
            i += 1
        blocks.append(Block("para", para))
    return blocks


def split_table_rows(block: Block) -> tuple[list[str], list[list[str]]]:
    rows = [row.strip() for row in block.lines]
    content = []
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        content.append(cells)
    if len(content) < 2:
        raise ValueError("table block too small")
    header = content[0]
    body = content[2:] if len(content) > 2 else []
    return header, body


def neurostate_figure(width: float) -> Drawing:
    fig_w = min(width, 460)
    fig_h = 150
    d = Drawing(fig_w, fig_h)

    def box(x, y, w, h, label, fill, stroke="#3A4A5A", fontsize=9.5):
        d.add(Rect(x, y, w, h, rx=8, ry=8, fillColor=colors.HexColor(fill), strokeColor=colors.HexColor(stroke), strokeWidth=1))
        d.add(String(x + w / 2, y + h / 2 - 3, label, textAnchor="middle", fontName="Helvetica-Bold", fontSize=fontsize, fillColor=colors.black))

    # main flow boxes
    box(10, 90, 96, 36, "User turn / tape", "#EEF4FB")
    box(126, 90, 118, 36, "CPOS state update\nctx7: calm, corruption", "#E8F2EA")
    box(266, 90, 90, 36, "Action gate", "#F3EEF8")
    box(388, 90, 62, 36, "PASS", "#E6F6EA")

    # warning path
    box(266, 34, 90, 36, "WARN", "#FFF1D9")
    box(388, 34, 62, 36, "EXEC\nblock", "#FBE3E3")

    # arrows
    arrows = [
        (106, 108, 126, 108),
        (244, 108, 266, 108),
        (356, 108, 388, 108),
        (311, 90, 311, 70),
        (356, 52, 388, 52),
        (419, 90, 419, 70),
    ]
    for x1, y1, x2, y2 in arrows:
        d.add(Line(x1, y1, x2, y2, strokeColor=colors.HexColor("#4B5563"), strokeWidth=1.2))

    # arrow heads
    d.add(Polygon(points=[382, 111, 388, 108, 382, 105], fillColor=colors.HexColor("#4B5563"), strokeColor=colors.HexColor("#4B5563")))
    d.add(Polygon(points=[382, 55, 388, 52, 382, 49], fillColor=colors.HexColor("#4B5563"), strokeColor=colors.HexColor("#4B5563")))
    d.add(Polygon(points=[263, 76, 266, 70, 269, 76], fillColor=colors.HexColor("#4B5563"), strokeColor=colors.HexColor("#4B5563")))

    d.add(String(318, 78, "dangerous EXEC?", textAnchor="middle", fontName="Helvetica-Bold", fontSize=9, fillColor=colors.HexColor("#374151")))
    d.add(String(290, 6, "C4: WARN + EXEC closes adaptive below-threshold attacks", textAnchor="middle", fontName="Helvetica", fontSize=8.2, fillColor=colors.HexColor("#555555")))
    return d


def is_separator_row(row: list[str]) -> bool:
    if not row:
        return False
    return all(set(cell.replace(":", "").replace("-", "").strip()) == set() for cell in row if cell)


def build_story(md_text: str, available_width: float):
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PaperTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=10,
    )
    subtitle_style = ParagraphStyle(
        "PaperSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#444444"),
        spaceAfter=10,
    )
    body_style = ParagraphStyle(
        "PaperBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=12.5,
        alignment=TA_LEFT,
        spaceAfter=6,
    )
    heading1_style = ParagraphStyle(
        "Heading1Paper",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#1B365D"),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True,
    )
    heading2_style = ParagraphStyle(
        "Heading2Paper",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=14,
        textColor=colors.HexColor("#1B365D"),
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True,
    )
    heading3_style = ParagraphStyle(
        "Heading3Paper",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor("#1B365D"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )
    code_style = ParagraphStyle(
        "PaperCode",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=8.2,
        leading=10,
        leftIndent=6,
        rightIndent=6,
        spaceBefore=3,
        spaceAfter=6,
    )

    blocks = parse_markdown_blocks(md_text)
    story = []
    title_done = False

    for idx, block in enumerate(blocks):
        if block.kind == "heading":
            text = block.lines[0]
            if text.startswith("# "):
                title = text[2:].strip()
                story.append(Spacer(1, 0.4 * inch))
                story.append(Paragraph(escape_text(title), title_style))
                title_done = True
            elif text.startswith("## "):
                story.append(Paragraph(escape_text(text[3:].strip()), heading1_style))
            elif text.startswith("### "):
                story.append(Paragraph(escape_text(text[4:].strip()), heading2_style))
            else:
                story.append(Paragraph(escape_text(text.lstrip("# ").strip()), heading3_style))
            continue

        if block.kind == "para":
            para = " ".join(line.strip() for line in block.lines).strip()
            if para:
                story.append(Paragraph(escape_text(para), body_style))
            continue

        if block.kind == "list":
            items = [ListItem(Paragraph(escape_text(item), body_style)) for item in block.lines]
            story.append(ListFlowable(items, bulletType="bullet", leftIndent=14))
            story.append(Spacer(1, 4))
            continue

        if block.kind.startswith("code:"):
            lang = block.kind.split(":", 1)[1]
            if lang == "mermaid":
                story.append(Spacer(1, 2))
                story.append(neurostate_figure(available_width))
                story.append(Spacer(1, 4))
            else:
                code_text = "\n".join(block.lines)
                story.append(Paragraph(escape_text(code_text).replace("\n", "<br/>"), code_style))
            continue

        if block.kind == "table":
            raw_rows = [row.strip() for row in block.lines]
            parsed = [[c.strip() for c in row.strip("|").split("|")] for row in raw_rows]
            if len(parsed) >= 2 and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in parsed[1]):
                header = parsed[0]
                body = parsed[2:]
            else:
                header = parsed[0]
                body = parsed[1:]
            rows = [header] + body
            table_data = [[Paragraph(escape_text(cell), body_style if r else heading3_style) for cell in row] for r, row in enumerate(rows)]
            widths = table_widths(rows, available_width)
            tbl = Table(table_data, colWidths=widths, repeatRows=1)
            tbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDE7F2")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1B365D")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8.7),
                        ("LEADING", (0, 0), (-1, -1), 10.5),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9AA8B6")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(tbl)
            story.append(Spacer(1, 8))
            continue

    if not title_done:
        story.insert(0, Paragraph("NeuroState as a Pre-LLM Execution Gate", title_style))
    return story


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, 0.55 * inch, f"{doc.page}")
    canvas.restoreState()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a PDF from the NeuroState paper draft markdown.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    md_text = args.input.read_text(encoding="utf-8")
    doc = SimpleDocTemplate(
        str(args.output),
        pagesize=letter,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.8 * inch,
        bottomMargin=0.7 * inch,
        title="NeuroState as a Pre-LLM Execution Gate",
        author="Aya Mizutani",
        subject="NeuroState ablation paper draft",
        creator="Codex",
    )
    story = build_story(md_text, doc.width)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

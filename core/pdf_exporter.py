"""
Craftora PDF Exporter
Generates professional, beautifully formatted pattern PDFs.
"""

import os
import uuid
from io import BytesIO
from typing import TYPE_CHECKING

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable

# Brand colors
PRIMARY   = HexColor("#B85C38")
ACCENT    = HexColor("#C9952A")
DARK      = HexColor("#1A1210")
LIGHT_BG  = HexColor("#FAF7F2")
DIVIDER   = HexColor("#E8DDD3")
SUCCESS   = HexColor("#4CAF50")
WARNING   = HexColor("#FFA726")
ERROR_COL = HexColor("#EF5350")

PDF_OUTPUT_DIR = "generated_pdfs"
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title",
            fontSize=28, textColor=PRIMARY, spaceAfter=6,
            fontName="Helvetica-Bold", alignment=TA_LEFT),
        "subtitle": ParagraphStyle("subtitle",
            fontSize=13, textColor=HexColor("#6B5C52"), spaceAfter=16,
            fontName="Helvetica"),
        "section_header": ParagraphStyle("section_header",
            fontSize=14, textColor=PRIMARY, spaceBefore=18, spaceAfter=8,
            fontName="Helvetica-Bold"),
        "body": ParagraphStyle("body",
            fontSize=11, textColor=DARK, spaceAfter=4,
            fontName="Helvetica", leading=16),
        "row_num": ParagraphStyle("row_num",
            fontSize=11, textColor=PRIMARY,
            fontName="Helvetica-Bold"),
        "row_text": ParagraphStyle("row_text",
            fontSize=11, textColor=DARK, leading=16,
            fontName="Helvetica"),
        "stitch_count": ParagraphStyle("stitch_count",
            fontSize=10, textColor=HexColor("#6B5C52"),
            fontName="Helvetica-Oblique"),
        "note": ParagraphStyle("note",
            fontSize=10, textColor=HexColor("#7B6B99"),
            fontName="Helvetica-Oblique", leftIndent=12),
        "tag": ParagraphStyle("tag",
            fontSize=10, textColor=white, fontName="Helvetica-Bold"),
        "footer": ParagraphStyle("footer",
            fontSize=9, textColor=HexColor("#AA9A8F"),
            alignment=TA_CENTER, fontName="Helvetica"),
        "tip": ParagraphStyle("tip",
            fontSize=11, textColor=HexColor("#5C3D1E"),
            fontName="Helvetica", leftIndent=12, leading=15),
    }


def _skill_color(level: str) -> HexColor:
    return {
        "beginner":     HexColor("#4CAF50"),
        "intermediate": HexColor("#FFA726"),
        "advanced":     HexColor("#EF5350"),
    }.get(level, PRIMARY)


def generate_pdf(pattern_data: dict) -> str:
    """
    Generate a PDF from pattern data dict.
    Returns the file path to the saved PDF.
    """
    filename = f"{PDF_OUTPUT_DIR}/craftora_{uuid.uuid4().hex[:8]}.pdf"
    buf      = BytesIO()
    doc      = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
    )

    s      = _styles()
    story  = []
    rows   = pattern_data.get("rows", [])
    mats   = pattern_data.get("materials", [])
    abbrs  = pattern_data.get("abbreviations", {})
    finish = pattern_data.get("finishing", [])
    tips   = pattern_data.get("tips", [])
    valid  = pattern_data.get("validation", {})

    # ── Header block ──────────────────────────────────────────────────────────
    craft_type  = pattern_data.get("craft_type", "").replace("_", " ").title()
    skill_level = pattern_data.get("skill_level", "beginner")
    skill_color = _skill_color(skill_level)

    # Craft emoji
    craft_emojis = {"Crochet": "🪝", "Knitting": "🧶", "Embroidery": "🪡", "Cross Stitch": "✚"}
    emoji = craft_emojis.get(craft_type, "✦")

    story.append(Paragraph(f"{emoji} {pattern_data.get('title', 'Untitled Pattern')}", s["title"]))
    story.append(Paragraph(pattern_data.get("description", ""), s["subtitle"]))

    # Meta tags row
    tag_data = [[
        Paragraph(f"  {craft_type}  ", s["tag"]),
        Paragraph(f"  {skill_level.title()}  ", s["tag"]),
        Paragraph(f"  {pattern_data.get('terminology', 'US')} Terms  ", s["tag"]),
        Paragraph(f"  ⏱ {pattern_data.get('estimated_time', '—')}  ", s["tag"]),
    ]]
    tag_style = TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), PRIMARY),
        ("BACKGROUND", (1, 0), (1, 0), skill_color),
        ("BACKGROUND", (2, 0), (2, 0), HexColor("#2C6B99")),
        ("BACKGROUND", (3, 0), (3, 0), ACCENT),
        ("ROUNDEDCORNERS", [4], [4], [4], [4]),
        ("FONTNAME",  (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",  (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (-1, -1), white),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ])
    story.append(Table(tag_data, style=tag_style, hAlign="LEFT"))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1, color=DIVIDER))
    story.append(Spacer(1, 8))

    # ── Quick info grid ───────────────────────────────────────────────────────
    info_items = [
        ("Hook/Needle", pattern_data.get("hook_or_needle") or "—"),
        ("Gauge",       pattern_data.get("gauge") or "—"),
        ("Finished Size", pattern_data.get("finished_size") or "—"),
        ("Yarn Weight", pattern_data.get("yarn_weight") or "—"),
    ]
    info_data  = [[Paragraph(f"<b>{k}</b><br/>{v}", s["body"]) for k, v in info_items]]
    info_table = Table(info_data, colWidths=["25%", "25%", "25%", "25%"])
    info_table.setStyle(TableStyle([
        ("BOX",        (0, 0), (-1, -1), 0.5, DIVIDER),
        ("INNERGRID",  (0, 0), (-1, -1), 0.5, DIVIDER),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("ALIGN",    (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",   (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT_BG]),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 16))

    # ── Materials ─────────────────────────────────────────────────────────────
    if mats:
        story.append(Paragraph("Materials", s["section_header"]))
        mat_rows = [["Item", "Amount", "Notes"]]
        for m in mats:
            mat_rows.append([
                m.get("name", ""),
                m.get("quantity", ""),
                m.get("notes", "") or "",
            ])
        mat_table = Table(mat_rows, colWidths=["40%", "25%", "35%"])
        mat_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR",     (0, 0), (-1, 0), white),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [white, LIGHT_BG]),
            ("GRID",          (0, 0), (-1, -1), 0.5, DIVIDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(mat_table)
        story.append(Spacer(1, 12))

    # ── Abbreviations ─────────────────────────────────────────────────────────
    if abbrs:
        story.append(Paragraph("Abbreviations", s["section_header"]))
        abbr_items = list(abbrs.items())
        # Two-column layout
        half = (len(abbr_items) + 1) // 2
        left  = abbr_items[:half]
        right = abbr_items[half:]
        abbr_rows = []
        for i in range(half):
            l = left[i]  if i < len(left)  else ("", "")
            r = right[i] if i < len(right) else ("", "")
            abbr_rows.append([
                Paragraph(f"<b>{l[0]}</b> = {l[1]}", s["body"]),
                Paragraph(f"<b>{r[0]}</b> = {r[1]}", s["body"]) if r[0] else Paragraph("", s["body"]),
            ])
        abbr_table = Table(abbr_rows, colWidths=["50%", "50%"])
        abbr_table.setStyle(TableStyle([
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [white, LIGHT_BG]),
            ("GRID",          (0, 0), (-1, -1), 0.5, DIVIDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ]))
        story.append(abbr_table)
        story.append(Spacer(1, 12))

    # ── Pattern Rows ──────────────────────────────────────────────────────────
    story.append(Paragraph("Pattern Instructions", s["section_header"]))

    for row in rows:
        row_num  = row.get("row_number", 0)
        instr    = row.get("instruction", "")
        count    = row.get("stitch_count", 0)
        note     = row.get("note") or row.get("notes", "")
        is_rep   = row.get("is_repeat", False)

        label = f"Round {row_num}" if "rnd" in instr.lower() else f"Row {row_num}"

        row_data = [[
            Paragraph(f"<b>{label}</b>", s["row_num"]),
            Paragraph(instr, s["row_text"]),
            Paragraph(f"({count} sts)", s["stitch_count"]),
        ]]
        row_table = Table(row_data, colWidths=["12%", "73%", "15%"])
        bg = HexColor("#FFF8F5") if not is_rep else HexColor("#F5F0FF")
        row_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), bg),
            ("LINEBELOW",     (0, 0), (-1, -1), 0.5, DIVIDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(row_table)

        if note:
            story.append(Paragraph(f"💡 {note}", s["note"]))

    story.append(Spacer(1, 16))

    # ── Finishing ─────────────────────────────────────────────────────────────
    if finish:
        story.append(Paragraph("Finishing", s["section_header"]))
        for i, step in enumerate(finish, 1):
            story.append(Paragraph(f"{i}. {step}", s["body"]))
        story.append(Spacer(1, 12))

    # ── Tips ──────────────────────────────────────────────────────────────────
    if tips:
        story.append(Paragraph("Tips & Notes", s["section_header"]))
        tips_data = [[Paragraph(
            "".join([f"<b>✦ Tip {i}:</b> {t}<br/>" for i, t in enumerate(tips, 1)]),
            s["tip"]
        )]]
        tips_table = Table(tips_data, colWidths=["100%"])
        tips_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), HexColor("#FFF8F0")),
            ("BOX",           (0, 0), (-1, -1), 1.5, ACCENT),
            ("TOPPADDING",    (0, 0), (-1, -1), 14),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ("LEFTPADDING",   (0, 0), (-1, -1), 16),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ]))
        story.append(tips_table)
        story.append(Spacer(1, 16))

    # ── Validation Summary ────────────────────────────────────────────────────
    if valid:
        score   = valid.get("score", 100)
        passed  = valid.get("passed", True)
        errors  = valid.get("errors", [])
        warnings = valid.get("warnings", [])

        score_color = SUCCESS if score >= 90 else (WARNING if score >= 70 else ERROR_COL)
        status_text = "✅ All checks passed" if passed else f"⚠ {len(errors)} issue(s) found"

        story.append(Paragraph("Pattern Validation", s["section_header"]))
        val_data = [[
            Paragraph(f"<b>Quality Score: {score}/100</b><br/>{status_text}", s["body"]),
        ]]
        for err in errors:
            val_data.append([Paragraph(f"🔴 {err.get('rule','')}: {err.get('message','')}", s["body"])])
        for w in warnings:
            val_data.append([Paragraph(f"🟡 {w.get('rule','')}: {w.get('message','')}", s["body"])])

        val_table = Table(val_data, colWidths=["100%"])
        val_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (0, 0), HexColor("#E8F5E9") if passed else HexColor("#FFF3E0")),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [HexColor("#FFEBEE"), HexColor("#FFF8E1")]),
            ("GRID",          (0, 0), (-1, -1), 0.5, DIVIDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ]))
        story.append(val_table)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 24))
    story.append(HRFlowable(width="100%", thickness=1, color=DIVIDER))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Generated by Craftora Pattern Studio  ·  craftora.app  ·  Pattern is for personal use only.",
        s["footer"]
    ))

    doc.build(story)

    with open(filename, "wb") as f:
        f.write(buf.getvalue())

    return filename

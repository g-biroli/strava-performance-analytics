import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PAGE_W, _ = A4
MARGIN    = 1.8 * cm
CONTENT_W = PAGE_W - 2 * MARGIN   # ~493 pt

_ORANGE = colors.HexColor("#FC4C02")
_CREAM  = colors.HexColor("#FFF4ED")
_GRAY   = colors.HexColor("#8E8E93")
_DARK   = colors.HexColor("#242428")


def build_pdf(
    section_title: str,
    d_start: str,
    d_end: str,
    kpis: list,
    fig_sections: list = None,   # kept for API compatibility — charts not rendered
    accent_hex: str = "#FC4C02",
) -> bytes:
    """
    Generates a fast, kaleido-free PDF report with a KPI summary table.
    kpis : [(label, value), ...]
    fig_sections is accepted but ignored (no kaleido dependency).
    """
    buf    = io.BytesIO()
    accent = colors.HexColor(accent_hex)
    styles = getSampleStyleSheet()

    s_title = ParagraphStyle(
        "rpt_title", parent=styles["Heading1"],
        textColor=accent, fontSize=22, spaceAfter=4, fontName="Helvetica-Bold",
    )
    s_meta = ParagraphStyle(
        "rpt_meta", parent=styles["Normal"],
        textColor=_GRAY, fontSize=10, spaceAfter=14,
    )
    s_note = ParagraphStyle(
        "rpt_note", parent=styles["Normal"],
        textColor=_GRAY, fontSize=9, fontName="Helvetica-Oblique", spaceAfter=6,
    )
    s_kpi_lbl = ParagraphStyle(
        "rpt_kpi_lbl", parent=styles["Normal"],
        textColor=_GRAY, fontSize=8, fontName="Helvetica", alignment=1,
    )
    s_kpi_val = ParagraphStyle(
        "rpt_kpi_val", parent=styles["Normal"],
        textColor=accent, fontSize=16, fontName="Helvetica-Bold", alignment=1,
    )

    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph(section_title, s_title))
    story.append(Paragraph(f"Period: {d_start}  →  {d_end}", s_meta))
    story.append(HRFlowable(width=CONTENT_W, color=accent, thickness=2, spaceAfter=16))

    # ── KPI table ─────────────────────────────────────────────────────────────
    if kpis:
        n     = len(kpis)
        col_w = CONTENT_W / n
        kpi_tbl = Table(
            [
                [Paragraph(lbl.upper(), s_kpi_lbl) for lbl, _ in kpis],
                [Paragraph(val,          s_kpi_val) for _, val in kpis],
            ],
            colWidths=[col_w] * n,
            rowHeights=[22, 36],
        )
        kpi_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), _CREAM),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
            ("BOX",           (0, 0), (-1, -1), 1.5, accent),
            ("LINEAFTER",     (0, 0), (-2, -1), 0.5, colors.HexColor("#00000025")),
        ]))
        story.append(kpi_tbl)
        story.append(Spacer(1, 18))

    story.append(Paragraph(
        "Full interactive charts are available in the Strava Performance Analytics dashboard.",
        s_note,
    ))

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=MARGIN,
        title=section_title,
        author="Strava Performance Analytics",
    )
    doc.build(story)
    return buf.getvalue()

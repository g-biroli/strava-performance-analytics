import io
from datetime import date

import plotly.io as pio
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PAGE_W, PAGE_H = A4
MARGIN    = 1.5 * cm
CONTENT_W = PAGE_W - 2 * MARGIN   # ~538 pt

_ORANGE = colors.HexColor("#FC4C02")
_CREAM  = colors.HexColor("#FFF4ED")
_GRAY   = colors.HexColor("#8E8E93")
_DARK   = colors.HexColor("#242428")
_WHITE  = colors.white
_LIGHT  = colors.HexColor("#F4F4F6")
_BG_SECTION = colors.HexColor("#FAFAFA")


def _fig_to_image(fig, width_pt: float = CONTENT_W, height_ratio: float = 0.42):
    """Render a Plotly figure to high-res PNG via kaleido. Returns Image flowable or None."""
    try:
        px_w = int(width_pt / 72 * 96)
        px_h = int(px_w * height_ratio)
        png  = pio.to_image(fig, format="png", width=px_w, height=px_h, scale=2)
        return Image(io.BytesIO(png), width=width_pt, height=width_pt * height_ratio)
    except Exception:
        return None


def _make_styles(accent: colors.Color):
    return {
        "brand": ParagraphStyle(
            "rpt_brand", textColor=_GRAY, fontSize=8, leading=11, spaceAfter=2,
            fontName="Helvetica",
        ),
        "title": ParagraphStyle(
            "rpt_title", textColor=accent, fontSize=22, leading=26, spaceAfter=4,
            fontName="Helvetica-Bold",
        ),
        "sub": ParagraphStyle(
            "rpt_sub", textColor=_GRAY, fontSize=10, leading=14, spaceAfter=12,
            fontName="Helvetica",
        ),
        "section": ParagraphStyle(
            "rpt_section", textColor=accent, fontSize=11, leading=15,
            spaceBefore=10, spaceAfter=4, fontName="Helvetica-Bold",
        ),
        "kpi_lbl": ParagraphStyle(
            "rpt_kpi_lbl", textColor=_GRAY, fontSize=7, leading=10,
            fontName="Helvetica", alignment=1,
        ),
        "kpi_val": ParagraphStyle(
            "rpt_kpi_val", textColor=accent, fontSize=16, leading=20,
            fontName="Helvetica-Bold", alignment=1,
        ),
        "missing": ParagraphStyle(
            "rpt_missing", textColor=_GRAY, fontSize=8, leading=10,
            fontName="Helvetica-Oblique",
        ),
        "footer": ParagraphStyle(
            "rpt_footer", textColor=_GRAY, fontSize=8, leading=10,
            fontName="Helvetica",
        ),
    }


def _render_chart_pair(story, pair, s_section, s_missing):
    """Two charts side by side in a 2-column table."""
    GAP   = 12
    img_w = (CONTENT_W - GAP) / 2
    col_w = CONTENT_W / 2

    cells_hdr = []
    cells_img = []
    for chart_title, fig in pair:
        cells_hdr.append(Paragraph(chart_title, s_section))
        img = _fig_to_image(fig, width_pt=img_w, height_ratio=0.75)
        cells_img.append(img if img else Paragraph("(not rendered)", s_missing))

    tbl = Table(
        [cells_hdr, cells_img],
        colWidths=[col_w, col_w],
    )
    tbl.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (0, -1),  GAP),
        ("RIGHTPADDING",  (1, 0), (1, -1),  0),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 6))


def build_pdf(
    section_title: str,
    d_start: str,
    d_end: str,
    kpis: list,
    fig_sections: list = None,
    accent_hex: str = "#FC4C02",
) -> bytes:
    """
    Full PDF report with KPI table + all charts.

    kpis        : [(label, value), ...]
    fig_sections: each entry can be:
        (chart_title, fig)                    — single full-width chart
        (chart_title, fig, height_ratio)      — single with custom height
        [(title1, fig1), (title2, fig2)]      — side-by-side pair
    """
    buf    = io.BytesIO()
    accent = colors.HexColor(accent_hex)
    s      = _make_styles(accent)

    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("Strava Performance Analytics", s["brand"]))
    story.append(Paragraph(section_title, s["title"]))
    story.append(Paragraph(f"Period: {d_start}  →  {d_end}", s["sub"]))
    story.append(HRFlowable(width=CONTENT_W, color=accent, thickness=2.5, spaceAfter=14))

    # ── KPI summary table ─────────────────────────────────────────────────────
    if kpis:
        n     = len(kpis)
        col_w = CONTENT_W / n
        kpi_tbl = Table(
            [
                [Paragraph(lbl.upper(), s["kpi_lbl"]) for lbl, _ in kpis],
                [Paragraph(val,         s["kpi_val"]) for _, val in kpis],
            ],
            colWidths=[col_w] * n,
            rowHeights=[20, 38],
        )
        kpi_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), _CREAM),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
            ("BOX",           (0, 0), (-1, -1), 2, accent),
            ("LINEAFTER",     (0, 0), (-2, -1), 0.5, colors.HexColor("#00000030")),
            ("ROWBACKGROUNDS",(0, 0), (-1, -1), [_LIGHT, _CREAM]),
        ]))
        story.append(kpi_tbl)
        story.append(Spacer(1, 20))

    # ── Charts ────────────────────────────────────────────────────────────────
    if fig_sections:
        story.append(HRFlowable(
            width=CONTENT_W, color=colors.HexColor("#00000015"),
            thickness=0.8, spaceAfter=10,
        ))
        for entry in fig_sections:
            # Side-by-side pair: list with exactly 2 (title, fig) tuples
            if isinstance(entry, list) and len(entry) == 2 and isinstance(entry[0], tuple):
                _render_chart_pair(story, entry, s["section"], s["missing"])
            else:
                # Single chart: (title, fig) or (title, fig, height_ratio)
                chart_title = entry[0]
                fig         = entry[1]
                h_ratio     = entry[2] if len(entry) > 2 else 0.42
                story.append(Paragraph(chart_title, s["section"]))
                img = _fig_to_image(fig, width_pt=CONTENT_W, height_ratio=h_ratio)
                if img:
                    story.append(img)
                else:
                    story.append(Paragraph("(Chart could not be rendered)", s["missing"]))
                story.append(Spacer(1, 10))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width=CONTENT_W, color=_GRAY, thickness=0.5, spaceAfter=5))
    story.append(Paragraph(
        f"Strava Performance Analytics  ·  Generated on {date.today().strftime('%Y-%m-%d')}",
        s["footer"],
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

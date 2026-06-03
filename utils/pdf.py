import io

import plotly.io as pio
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
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

PAGE_W, _ = A4
MARGIN    = 1.8 * cm
CONTENT_W = PAGE_W - 2 * MARGIN   # ~493 pt

_ORANGE = colors.HexColor("#FC4C02")
_CREAM  = colors.HexColor("#FFF4ED")
_GRAY   = colors.HexColor("#8E8E93")
_DARK   = colors.HexColor("#242428")
_ICE    = colors.HexColor("#F4F4F6")


def _fig_to_image(fig, width_pt: float = CONTENT_W, height_ratio: float = 0.44):
    px_w = int(width_pt / 72 * 150)
    px_h = int(px_w * height_ratio)
    png  = pio.to_image(fig, format="png", width=px_w, height=px_h, scale=1)
    return Image(io.BytesIO(png), width=width_pt, height=width_pt * height_ratio)


def build_pdf(
    section_title: str,
    d_start: str,
    d_end: str,
    kpis: list,
    fig_sections: list,
    accent_hex: str = "#FC4C02",
) -> bytes:
    """
    kpis        : [(label, value), ...]
    fig_sections: [(chart_title, plotly_figure), ...]
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
    s_section = ParagraphStyle(
        "rpt_section", parent=styles["Heading2"],
        textColor=accent, fontSize=13, spaceBefore=20, spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    s_kpi_lbl = ParagraphStyle(
        "rpt_kpi_lbl", parent=styles["Normal"],
        textColor=_GRAY, fontSize=7, fontName="Helvetica", alignment=1,
    )
    s_kpi_val = ParagraphStyle(
        "rpt_kpi_val", parent=styles["Normal"],
        textColor=accent, fontSize=15, fontName="Helvetica-Bold", alignment=1,
    )
    s_warn = ParagraphStyle(
        "rpt_warn", parent=styles["Normal"],
        textColor=_GRAY, fontSize=9, fontName="Helvetica-Oblique",
    )

    story = []

    # ── Cabeçalho ─────────────────────────────────────────────────────────────
    story.append(Paragraph(section_title, s_title))
    story.append(Paragraph(f"Período: {d_start}  →  {d_end}", s_meta))
    story.append(HRFlowable(width=CONTENT_W, color=accent, thickness=2, spaceAfter=14))

    # ── KPIs ──────────────────────────────────────────────────────────────────
    if kpis:
        n     = len(kpis)
        col_w = CONTENT_W / n
        kpi_tbl = Table(
            [
                [Paragraph(lbl.upper(), s_kpi_lbl) for lbl, _ in kpis],
                [Paragraph(val,          s_kpi_val) for _, val in kpis],
            ],
            colWidths=[col_w] * n,
        )
        kpi_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), _CREAM),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
            ("BOX",           (0, 0), (-1, -1), 1.5, accent),
            ("LINEAFTER",     (0, 0), (-2, -1), 0.5, colors.HexColor("#FC4C0250")),
        ]))
        story.append(kpi_tbl)
        story.append(Spacer(1, 18))

    # ── Gráficos ──────────────────────────────────────────────────────────────
    for chart_title, fig in fig_sections:
        story.append(Paragraph(chart_title, s_section))
        try:
            story.append(_fig_to_image(fig, width_pt=CONTENT_W, height_ratio=0.44))
        except Exception as exc:
            story.append(Paragraph(f"(Gráfico indisponível: {exc})", s_warn))
        story.append(Spacer(1, 8))

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=MARGIN,
        title=section_title,
        author="Strava Performance Analytics",
    )
    doc.build(story)
    return buf.getvalue()

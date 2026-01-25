from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.lib.pagesizes import A4

from .part_a import draw_part_a
from .part_b import draw_part_b


def generate_form16_pdf(employee, company, financial_year, summary):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    # PART A (TDS)
    draw_part_a(
        c,
        employee=employee,
        company=company,
        fy=financial_year,
        tds_quarters=summary["tds_quarters"]
    )

    # PART B – OLD REGIME
    draw_part_b(
        c,
        summary=summary["old_regime"],
        fy=financial_year,
        regime_label="Old Regime"
    )

    # PART B – NEW REGIME
    draw_part_b(
        c,
        summary=summary["new_regime"],
        fy=financial_year,
        regime_label="New Regime"
    )

    c.save()
    buffer.seek(0)
    return buffer.getvalue()

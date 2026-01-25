from .utils import *

def draw_part_b(c, summary, fy, regime_label):
    y = TOP

    center(c, y, "FORM NO. 16 – PART B", True, 14)
    y -= LINE
    center(c, y, "Annexure to Part A", True)
    y -= LINE * 2

    text(c, LEFT, y, f"Financial Year: {fy}")
    y -= LINE
    text(c, LEFT, y, f"Tax Regime: {regime_label}", True)

    y -= LINE * 2

    rows = [
        ["Particulars", "Amount (₹)"],
        ["Gross Salary", summary["gross_salary"]],
        ["Exempt Allowances u/s 10", summary["exempt_allowances"]],
        ["Income Chargeable", summary["taxable_income"]],
        ["Deductions (Chapter VI-A)", summary["chapter_6a"]],
        ["Total Income", summary["total_income"]],
        ["Tax on Total Income", summary["tax_on_income"]],
        ["Health & Education Cess", summary["cess"]],
        ["Total Tax Payable", summary["total_tax"]],
        ["Tax Deducted at Source", summary["tax_deducted"]],
    ]

    rows = [
        [r[0], f"{r[1]:,.2f}"] if isinstance(r[1], (int, float)) else r
        for r in rows
    ]

    table(c, LEFT, y, [100 * mm, 40 * mm], rows)

    y -= LINE * (len(rows) + 2)
    text(
        c,
        LEFT,
        y,
        "This is a system generated Form-16. No signature is required.",
        size=9
    )

    c.showPage()

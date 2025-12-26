from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, black
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
)


PRIMARY = HexColor("#0f766e")   # matches your UI theme
LIGHT_BG = HexColor("#f0fdfa")


def generate_payslip_pdf(context: dict) -> BytesIO:
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    elements = []

    # =========================
    # HEADER
    # =========================
    elements.append(
        Paragraph(
            f"<b><font size=16 color='#0f766e'>{context['company_name']}</font></b>",
            styles["Title"]
        )
    )

    elements.append(
        Paragraph(
            f"Payslip for <b>{context['pay_period']}</b>",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 12))

    # =========================
    # EMPLOYEE INFO
    # =========================
    emp_table = Table(
        [
            ["Employee Name", context["employee_name"]],
            ["Employee ID", context["employee_id"]],
            ["Department", context["department"]],
            ["Pay Date", context["pay_date"]],
        ],
        colWidths=[120, 350]
    )

    emp_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, black),
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
        ("FONT", (0, 0), (-1, -1), "Helvetica"),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(emp_table)
    elements.append(Spacer(1, 16))

    # =========================
    # EARNINGS / DEDUCTIONS
    # =========================
    salary_table = Table(
        [
            ["EARNINGS", "Amount (₹)", "DEDUCTIONS", "Amount (₹)"],
            ["Basic Salary", context["basic_salary"], "Provident Fund", context["pf"]],
            ["HRA", context["hra"], "Professional Tax", context["professional_tax"]],
            ["Transport Allowance", context["transport"], "Income Tax", context["income_tax"]],
            ["Overtime", context["overtime"], "", ""],
            ["Bonus", context["bonus"], "", ""],
            ["", "", "", ""],
            ["Gross Salary", context["gross_salary"], "Total Deductions", context["total_deductions"]],
        ],
        colWidths=[150, 100, 150, 100]
    )

    salary_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, black),
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BG),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONT", (0, 1), (-1, -1), "Helvetica"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(salary_table)
    elements.append(Spacer(1, 16))

    # =========================
    # NET PAY (HIGHLIGHTED)
    # =========================
    net_pay_table = Table(
        [["NET PAY", f"₹ {context['net_pay']}"]],
        colWidths=[300, 200]
    )

    net_pay_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, PRIMARY),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("FONT", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 10),
    ]))

    elements.append(net_pay_table)
    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            "<i>This is a system-generated payslip and does not require a signature.</i>",
            styles["Normal"]
        )
    )

    doc.build(elements)
    buffer.seek(0)
    return buffer

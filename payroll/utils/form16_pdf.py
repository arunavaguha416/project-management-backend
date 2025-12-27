from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, lightgrey
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime

def short_id(value, length=18):
    value = str(value)
    return value if len(value) <= length else value[:length] + "..."


PRIMARY = HexColor("#0f766e")   # Enterprise teal
DARK = HexColor("#111827")
GREY = HexColor("#6b7280")
BORDER = HexColor("#e5e7eb")
BG_LIGHT = HexColor("#f9fafb")


def draw_section_box(c, x, y, w, h, title):
    c.setStrokeColor(BORDER)
    c.setFillColor(BG_LIGHT)
    c.rect(x, y - h, w, h, fill=1)

    c.setFillColor(PRIMARY)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 10, y - 18, title)


def draw_kv(c, x, y, label, value):
    c.setFont("Helvetica", 9)
    c.setFillColor(GREY)
    c.drawString(x, y, label)

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(DARK)
    c.drawRightString(x + 240, y, value)


def generate_form16_pdf(employee, company, financial_year, summary):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # ================= HEADER =================
    c.setFillColor(PRIMARY)
    c.rect(0, height - 80, width, 80, fill=1)

    c.setFillColor("white")
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 45, company.name)

    c.setFont("Helvetica", 10)
    c.drawString(40, height - 65, "FORM 16 – Salary Certificate (Part B)")
    c.drawRightString(width - 40, height - 65, f"FY {financial_year}")

    y = height - 110

    # ================= EMPLOYEE DETAILS =================
    draw_section_box(c, 40, y, width - 80, 90, "Employee Details")

    draw_kv(c, 50, y - 40, "Employee Name", employee.user.name)
    draw_kv(
    c,
    330,
    y - 40,
    "Employee ID",
    short_id(employee.id)
)


    draw_kv(
        c, 50, y - 60,
        "Department",
        employee.department.name if employee.department else "-"
    )
    draw_kv(c, 330, y - 60, "Company", company.name)

    y -= 120

    # ================= SALARY DETAILS =================
    draw_section_box(c, 40, y, width - 80, 170, "Salary & Tax Computation")

    left_x = 50
    right_x = 330
    row_y = y - 40

    rows_left = [
        ("Gross Salary", summary["gross_salary"]),
        ("Taxable Income", summary["taxable_income"]),
        ("Provident Fund (80C)", summary["provident_fund"]),
    ]

    rows_right = [
        ("Professional Tax", summary["professional_tax"]),
        ("Total Tax Deducted", summary["total_tax"]),
    ]

    for label, value in rows_left:
        draw_kv(c, left_x, row_y, label, f"₹ {value:,.2f}")
        row_y -= 18

    row_y = y - 40
    for label, value in rows_right:
        draw_kv(c, right_x, row_y, label, f"₹ {value:,.2f}")
        row_y -= 18

    # ================= NET PAY HIGHLIGHT =================
    c.setStrokeColor(PRIMARY)
    c.setFillColor(HexColor("#ecfeff"))
    c.rect(40, y - 160, width - 80, 40, fill=1)

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(PRIMARY)
    c.drawString(50, y - 135, "Net Salary Paid")

    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(
        width - 50,
        y - 135,
        f"₹ {summary['net_salary']:,.2f}"
    )

    y -= 210

    # ================= FOOTER =================
    c.setFont("Helvetica", 8)
    c.setFillColor(GREY)
    c.drawString(
        40,
        y,
        "This is a system-generated Form-16. No signature is required."
    )

    c.drawRightString(
        width - 40,
        y,
        f"Generated on {datetime.now().strftime('%d %b %Y')}"
    )

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer.getvalue()

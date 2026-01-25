from .utils import *

def draw_part_a(c, employee, company, fy, tds_quarters):
    y = TOP

    center(c, y, "FORM NO. 16", True, 14)
    y -= LINE
    center(c, y, "[See rule 31(1)(a)]")
    y -= LINE
    center(
        c,
        y,
        "Certificate under Section 203 of the Income-tax Act, 1961",
        True
    )

    y -= LINE * 2

    rows = [
        ["Employer Name & Address", f"{company.name}"],
        ["Employee Name & Address", f"{employee.user.name}"],
        ["PAN of Employer", company.pan],
        ["TAN of Employer", company.tan],
        ["PAN of Employee", employee.pan],
        ["Assessment Year", fy],
        ["Period of Employment", fy],
    ]

    y = table(c, LEFT, y, [80 * mm, 90 * mm], rows, 22)

    y -= LINE * 2
    text(c, LEFT, y, "Summary of tax deducted at source", True)
    y -= LINE

    rows = [["Quarter", "Gross Salary", "TDS Deducted"]]

    for q in tds_quarters:
        rows.append([
            q["quarter"],
            f"{q['gross']:,.2f}",
            f"{q['tds']:,.2f}"
        ])

    table(c, LEFT, y, [40 * mm, 60 * mm, 60 * mm], rows)

    y -= LINE * 4
    text(
        c,
        LEFT,
        y,
        "This Part-A is system generated and is valid without signature.",
        size=9
    )

    c.showPage()

from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black
from reportlab.lib.units import mm

PAGE_WIDTH, PAGE_HEIGHT = A4

LEFT = 20 * mm
RIGHT = PAGE_WIDTH - 20 * mm
TOP = PAGE_HEIGHT - 20 * mm
BOTTOM = 20 * mm

LINE = 14


def text(c, x, y, value, bold=False, size=10):
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.setFillColor(black)
    c.drawString(x, y, str(value))


def center(c, y, value, bold=False, size=11):
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawCentredString(PAGE_WIDTH / 2, y, str(value))


def table(c, x, y, widths, rows, h=14):
    cur_y = y
    for row in rows:
        cur_x = x
        for i, cell in enumerate(row):
            c.rect(cur_x, cur_y - h, widths[i], h)
            c.drawString(cur_x + 4, cur_y - h + 4, str(cell))
            cur_x += widths[i]
        cur_y -= h
    return cur_y

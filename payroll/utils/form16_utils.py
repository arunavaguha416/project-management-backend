from django.db.models import Sum
from payroll.models import Payroll
from datetime import date


def generate_form16_summary(employee, financial_year):
    """
    Generates Form-16 summary (Part-A + Part-B)
    Financial year format: "2025-2026"
    """

    start_year, end_year = map(int, financial_year.split("-"))

    fy_start = date(start_year, 4, 1)
    fy_end = date(end_year, 3, 31)

    payrolls = Payroll.objects.filter(
        employee=employee,
        pay_run__status="FINALIZED",
        payroll_period__start_date__gte=fy_start,
        payroll_period__start_date__lte=fy_end,
        deleted_at__isnull=True
    )

    # ==============================
    # PART-A : QUARTERLY TDS SUMMARY
    # ==============================
    quarters = {
        "Q1": (4, 6),
        "Q2": (7, 9),
        "Q3": (10, 12),
        "Q4": (1, 3),
    }

    tds_quarters = []

    for q, (start_m, end_m) in quarters.items():
        qs = payrolls.filter(
            payroll_period__start_date__month__gte=start_m,
            payroll_period__start_date__month__lte=end_m
        )

        agg = qs.aggregate(
            gross=Sum("gross_salary"),
            tds=Sum("income_tax")
        )

        tds_quarters.append({
            "quarter": q,
            "gross": agg["gross"] or 0,
            "tds": agg["tds"] or 0
        })

    # ==============================
    # COMMON AGGREGATES
    # ==============================
    agg = payrolls.aggregate(
        gross_salary=Sum("gross_salary"),
        provident_fund=Sum("provident_fund"),
        professional_tax=Sum("professional_tax"),
        income_tax=Sum("income_tax"),
        net_salary=Sum("net_salary"),
    )

    gross_salary = agg["gross_salary"] or 0
    provident_fund = agg["provident_fund"] or 0
    professional_tax = agg["professional_tax"] or 0
    income_tax = agg["income_tax"] or 0
    net_salary = agg["net_salary"] or 0

    # ==============================
    # PART-B : OLD REGIME
    # ==============================
    old_regime = _compute_old_regime(
        gross_salary,
        provident_fund,
        professional_tax,
        income_tax
    )

    # ==============================
    # PART-B : NEW REGIME
    # (No 80C / exemptions assumed)
    # ==============================
    new_regime = _compute_new_regime(
        gross_salary,
        income_tax
    )

    return {
        "tds_quarters": tds_quarters,
        "old_regime": old_regime,
        "new_regime": new_regime,
    }


def _compute_old_regime(gross, pf, prof_tax, tax_deducted):
    """
    Old tax regime computation (simplified but compliant)
    """

    standard_deduction = 50000
    chapter_6a = pf  # PF assumed as 80C

    taxable_income = (
        gross
        - standard_deduction
        - chapter_6a
        - prof_tax
    )

    taxable_income = max(taxable_income, 0)

    cess = round(tax_deducted * 0.04, 2)

    return {
        "gross_salary": gross,
        "exempt_allowances": standard_deduction,
        "taxable_income": taxable_income,
        "chapter_6a": chapter_6a,
        "total_income": taxable_income,
        "tax_on_income": tax_deducted,
        "cess": cess,
        "total_tax": tax_deducted + cess,
        "tax_deducted": tax_deducted,
    }


def _compute_new_regime(gross, tax_deducted):
    """
    New regime – no deductions
    """

    taxable_income = gross
    cess = round(tax_deducted * 0.04, 2)

    return {
        "gross_salary": gross,
        "exempt_allowances": 0,
        "taxable_income": taxable_income,
        "chapter_6a": 0,
        "total_income": taxable_income,
        "tax_on_income": tax_deducted,
        "cess": cess,
        "total_tax": tax_deducted + cess,
        "tax_deducted": tax_deducted,
    }

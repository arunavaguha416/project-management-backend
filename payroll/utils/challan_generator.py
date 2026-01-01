# payroll/utils/challan_generator.py

from datetime import date
from payroll.models.statutory_challan import StatutoryChallan
from django.db.models import Sum
from django.utils.timezone import now
from django.db import models   # ✅ REQUIRED



def generate_statutory_challans(payrun, payrolls):
    """
    Auto-generate PF / PT / TDS challans for a finalized PayRun
    """

    # ✅ Derive company safely
    first_payroll = payrolls.first()
    if not first_payroll or not first_payroll.employee or not first_payroll.employee.company:
        raise Exception("Company could not be determined for challan generation")

    company = first_payroll.employee.company

    month = payrun.payroll_period.start_date.month
    year = payrun.payroll_period.start_date.year

    # ===============================
    # PF CHALLAN
    # ===============================
    pf_amount = payrolls.aggregate(
        total=models.Sum("provident_fund")
    )["total"] or 0

    if pf_amount > 0:
        StatutoryChallan.objects.get_or_create(
            company=company,
            statutory_type="PF",
            month=month,
            year=year,
            defaults={
                "amount": pf_amount,
                "due_date": date(year, month, 15),
                "status": "DUE"
            }
        )

    # ===============================
    # PT CHALLAN
    # ===============================
    pt_amount = payrolls.aggregate(
        total=models.Sum("professional_tax")
    )["total"] or 0

    if pt_amount > 0:
        StatutoryChallan.objects.get_or_create(
            company=company,
            statutory_type="PT",
            month=month,
            year=year,
            defaults={
                "amount": pt_amount,
                "due_date": date(year, month, 20),
                "status": "DUE"
            }
        )

    # ===============================
    # TDS CHALLAN
    # ===============================
    tds_amount = payrolls.aggregate(
        total=models.Sum("income_tax")
    )["total"] or 0

    if tds_amount > 0:
        StatutoryChallan.objects.get_or_create(
            company=company,
            statutory_type="TDS",
            month=month,
            year=year,
            defaults={
                "amount": tds_amount,
                "due_date": date(year, month, 7),
                "status": "DUE"
            }
        )


# payroll/utils/challan_generator.py

from payroll.models.statutory_challan import StatutoryChallan
from django.db.models import Sum
from django.utils.timezone import now

def generate_statutory_challans(payrun, payrolls):
    company = payrun.company
    period = payrun.payroll_period

    aggregates = payrolls.aggregate(
        pf=Sum("provident_fund"),
        pt=Sum("professional_tax"),
        tds=Sum("income_tax"),
    )

    challan_map = {
        "PF": aggregates["pf"] or 0,
        "PT": aggregates["pt"] or 0,
        "TDS": aggregates["tds"] or 0,
    }

    for key, amount in challan_map.items():
        if amount <= 0:
            continue

        StatutoryChallan.objects.get_or_create(
            company=company,
            statutory_type=key,
            month=period.start_date.month,
            year=period.start_date.year,
            defaults={
                "amount": amount,
                "due_date": now().date().replace(day=15),
                "status": "DUE"
            }
        )

from decimal import Decimal
from payroll.models import TaxConfiguration

def calculate_monthly_tax(gross_salary: Decimal) -> Decimal:
    """
    Calculates monthly income tax based on active tax slabs
    """
    slabs = TaxConfiguration.objects.filter(
        is_active=True,
        deleted_at__isnull=True
    ).order_by('min_amount')

    remaining_income = gross_salary
    tax = Decimal('0.00')

    for slab in slabs:
        if remaining_income <= 0:
            break

        slab_range = slab.max_amount - slab.min_amount
        taxable_amount = min(remaining_income, slab_range)

        slab_tax = taxable_amount * (slab.tax_percentage / Decimal('100'))
        tax += slab_tax

        remaining_income -= taxable_amount

    return tax.quantize(Decimal('0.01'))

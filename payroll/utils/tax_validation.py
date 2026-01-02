from payroll.models import TaxConfiguration


def validate_full_tax_slab_set():
    """
    Validates that at least one active tax configuration exists
    and that its JSON slab structure is valid.
    """

    tax_config = (
        TaxConfiguration.objects
        .filter(is_active=True, deleted_at__isnull=True)
        .first()
    )

    if not tax_config:
        raise Exception("No active tax configuration found")

    if not tax_config.tax_slabs:
        raise Exception("Tax slabs JSON is missing")

    slabs = tax_config.tax_slabs

    if not isinstance(slabs, list):
        raise Exception("Tax slabs must be a list")

    previous_to = None

    for slab in slabs:
        if not all(k in slab for k in ("from", "to", "rate")):
            raise Exception("Each tax slab must have from, to and rate")

        if slab["from"] >= slab["to"]:
            raise Exception("Invalid slab range")

        if previous_to is not None and slab["from"] != previous_to:
            raise Exception("Tax slabs are not continuous")

        previous_to = slab["to"]

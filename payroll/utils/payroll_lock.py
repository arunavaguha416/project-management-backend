

from rest_framework.exceptions import ValidationError

def ensure_payroll_not_locked(payroll):
    if payroll.pay_run.status == "FINALIZED":
        raise ValidationError("Payroll is locked after finalization")

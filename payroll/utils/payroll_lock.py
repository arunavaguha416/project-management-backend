
from django.utils import timezone
from rest_framework.exceptions import ValidationError

def ensure_payroll_not_locked(payroll):
    if payroll.pay_run.status == "FINALIZED":
        raise ValidationError("Payroll is locked after finalization")
    
def lock_payrun(payrun, reason):
    payrun.is_locked = True
    payrun.locked_reason = reason
    payrun.locked_at = timezone.now()
    payrun.save(update_fields=['is_locked', 'locked_reason', 'locked_at'])

def unlock_payrun(payrun):
    payrun.is_locked = False
    payrun.locked_reason = None
    payrun.locked_at = None
    payrun.save(update_fields=['is_locked', 'locked_reason', 'locked_at'])


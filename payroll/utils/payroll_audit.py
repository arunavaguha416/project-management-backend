from payroll.models.payroll_models import PayrollAuditLog


def log_payroll_change(payroll, field, old, new, user):
    if str(old) == str(new):
        return

    PayrollAuditLog.objects.create(
        payroll=payroll,
        field_name=field,
        old_value=str(old),
        new_value=str(new),
        changed_by=user
    )

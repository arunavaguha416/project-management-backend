# payroll/utils/company_context.py


from hr_management.models.hr_management_models import Employee


def get_company_from_request(request):
    employee = Employee.objects.filter(
        user=request.user,
        deleted_at__isnull=True
    ).first()

    if not employee or not employee.company:
        return None

    return employee.company

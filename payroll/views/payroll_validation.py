# payroll/views/payroll_validation.py

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from payroll.models.payroll_models import Payroll, PayRun
from hr_management.models.hr_management_models import Employee


class PayrollValidationView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            pay_run_id = request.data.get("pay_run_id")
            if not pay_run_id:
                return Response(
                    {"status": False, "message": "pay_run_id is required"},
                    status=400
                )

            payrun = PayRun.objects.filter(id=pay_run_id).first()
            if not payrun:
                return Response(
                    {"status": False, "message": "Pay Run not found"},
                    status=404
                )

            if payrun.status == "FINALIZED":
                return Response(
                    {"status": False, "message": "Pay Run already finalized"},
                    status=400
                )

            payrolls = Payroll.objects.select_related(
                "employee",
                "employee__user"
            ).filter(pay_run=payrun)

            if not payrolls.exists():
                return Response({
                    "status": False,
                    "errors": ["No employees found in this pay run"]
                })

            errors = []

            for p in payrolls:
                emp = p.employee
                emp_errors = []

                if p.basic_salary <= 0:
                    emp_errors.append("Basic salary is zero or missing")

                if p.net_salary <= 0:
                    emp_errors.append("Net salary is zero or negative")

                if p.gross_salary < p.total_deductions:
                    emp_errors.append("Total deductions exceed gross salary")

                if not getattr(emp, "bank_account_no", None):
                    emp_errors.append("Bank account number missing")

                if not getattr(emp, "bank_ifsc", None):
                    emp_errors.append("Bank IFSC missing")

                if p.payable_days <= 0:
                    emp_errors.append("Payable days invalid")

                if emp_errors:
                    errors.append({
                        "employee_id": str(emp.id),
                        "employee_name": emp.user.name,
                        "issues": emp_errors
                    })

            if errors:
                return Response({
                    "status": False,
                    "errors": errors
                })

            return Response({
                "status": True,
                "message": "Payroll validation passed"
            })

        except Exception as e:
            return Response({
                "status": False,
                "message": "Payroll validation failed",
                "error": str(e)
            }, status=500)

# payroll/views/payroll_ai_views.py

import hashlib
import re
from django.core.cache import cache
from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from payroll.models.payroll_models import Payroll, PayRun, PayrollPeriod
from hr_management.models.hr_management_models import Employee


class PayrollAIChatView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            user = request.user
            role = (user.role or "USER").upper()
            pay_run_id = request.data.get("pay_run_id")
            message = (request.data.get("message") or "").strip()

            if not pay_run_id:
                return Response({"status": False, "message": "pay_run_id is required"}, status=400)

            if role not in ["HR", "ADMIN", "MANAGER"]:
                return Response(
                    {"status": True, "records": {"reply": "Payroll AI is available only to HR, Admin, or Manager roles."}},
                    status=200
                )

            msg = message.lower()

            def _qkey(text: str) -> str:
                clean = re.sub(r"\s+", " ", (text or "").strip().lower())
                digest = hashlib.sha256(clean.encode("utf-8")).hexdigest()[:16]
                return f"ai:payroll:{user.id}:{pay_run_id}:{digest}"

            cached = cache.get(_qkey(message))
            if cached:
                return Response({"status": True, "records": {"reply": cached, "cached": True}}, status=200)

            payrun = PayRun.objects.select_related("payroll_period").filter(id=pay_run_id).first()
            if not payrun:
                return Response({"status": False, "message": "Pay Run not found"}, status=404)

            payrolls = Payroll.objects.filter(pay_run=payrun)
            total_count = payrolls.count()
            approved_count = payrolls.filter(status="APPROVED").count()
            pending_count = total_count - approved_count

            net_total = payrolls.aggregate(total=Sum("net_salary")).get("total") or 0

            if "pending" in msg or "approval" in msg:
                reply = f"{pending_count} approval(s) pending out of {total_count} payroll(s)."
                cache.set(_qkey(message), reply, timeout=1800)
                return Response({"status": True, "records": {"reply": reply}}, status=200)

            if "net pay" in msg or "total net" in msg:
                reply = f"Total net pay for this run is ₹ {net_total:.2f}."
                cache.set(_qkey(message), reply, timeout=1800)
                return Response({"status": True, "records": {"reply": reply}}, status=200)

            if "validation" in msg or "issue" in msg:
                errors = []
                for p in payrolls.select_related("employee", "employee__user"):
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
                        errors.append({"employee_name": emp.user.name if emp.user else "Employee", "issues": emp_errors})

                if not errors:
                    reply = "Validation passed. No issues found."
                else:
                    sample = errors[:3]
                    sample_text = "; ".join([f"{e['employee_name']}: {', '.join(e['issues'])}" for e in sample])
                    reply = f"Validation found {len(errors)} employee(s) with issues. Sample: {sample_text}."
                cache.set(_qkey(message), reply, timeout=1800)
                return Response({"status": True, "records": {"reply": reply}}, status=200)

            if "variance" in msg:
                current_period = payrun.payroll_period
                previous_period = PayrollPeriod.objects.filter(start_date__lt=current_period.start_date).order_by("-start_date").first()
                if not previous_period:
                    reply = "No variance available (first payroll period)."
                else:
                    previous_payrun = PayRun.objects.filter(payroll_period=previous_period, status="FINALIZED").first()
                    if not previous_payrun:
                        reply = "No variance available (previous pay run not finalized)."
                    else:
                        current_employee = Employee.objects.filter(user=user, deleted_at__isnull=True).first()
                        company = current_employee.company if current_employee else None
                        current_payrolls = Payroll.objects.filter(pay_run=payrun)
                        previous_payrolls = Payroll.objects.filter(pay_run=previous_payrun)
                        if company:
                            current_payrolls = current_payrolls.filter(employee__company=company)
                            previous_payrolls = previous_payrolls.filter(employee__company=company)
                        prev_map = {p.employee_id: p for p in previous_payrolls}
                        variance = []
                        for p in current_payrolls:
                            prev = prev_map.get(p.employee_id)
                            if not prev:
                                continue
                            diff = p.net_salary - prev.net_salary
                            if diff != 0:
                                variance.append(diff)
                        reply = f"Variance records: {len(variance)} employee(s) with net salary changes."
                cache.set(_qkey(message), reply, timeout=1800)
                return Response({"status": True, "records": {"reply": reply}}, status=200)

            reply = (
                "Payroll AI can answer: pending approvals, total net pay, validation issues, or variance summary. "
                "Try asking one of those."
            )
            cache.set(_qkey(message), reply, timeout=1800)
            return Response({"status": True, "records": {"reply": reply}}, status=200)

        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=400)

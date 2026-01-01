from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from payroll.models.payroll_models import PayRun, PayrollRollbackLog


class PayrollRollbackView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            pay_run_id = request.data.get("pay_run_id")
            reason = request.data.get("reason")

            if not pay_run_id or not reason:
                return Response(
                    {
                        "status": False,
                        "message": "pay_run_id and reason are required"
                    },
                    status=400
                )

            payrun = PayRun.objects.filter(id=pay_run_id).first()
            if not payrun:
                return Response(
                    {"status": False, "message": "Pay Run not found"},
                    status=404
                )

            if payrun.status != "FINALIZED":
                return Response(
                    {
                        "status": False,
                        "message": "Only finalized pay runs can be rolled back"
                    },
                    status=400
                )

            # 🔒 Rollback action
            old_status = payrun.status
            payrun.status = "IN_PROGRESS"
            payrun.save(update_fields=["status"])

            # 🧾 Audit rollback
            PayrollRollbackLog.objects.create(
                pay_run=payrun,
                rolled_back_by=request.user,
                reason=reason
            )

            return Response({
                "status": True,
                "message": "Pay Run rolled back successfully",
                "previous_status": old_status,
                "current_status": payrun.status
            })

        except Exception as e:
            return Response({
                "status": False,
                "message": "Payroll rollback failed",
                "error": str(e)
            }, status=500)

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from payroll.models.payroll_models import PayrollAuditLog


class PayrollAuditTrailView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        payroll_id = request.data.get("payroll_id")

        if not payroll_id:
            return Response(
                {"status": False, "message": "payroll_id is required"},
                status=400
            )

        logs = PayrollAuditLog.objects.select_related(
            "changed_by"
        ).filter(
            payroll_id=payroll_id
        )

        data = []
        for log in logs:
            data.append({
                "field": log.field_name,
                "old": log.old_value,
                "new": log.new_value,
                "changed_by": log.changed_by.username if log.changed_by else "-",
                "changed_at": log.changed_at
            })

        return Response({
            "status": True,
            "records": data
        })

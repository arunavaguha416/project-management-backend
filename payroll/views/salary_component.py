
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q, Sum, Count, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid
import os
import pytesseract
from PIL import Image
import io
import base64

from payroll.models.expense_models import ExpenseCategory, ExpenseClaim, ExpenseApprovalWorkflow
from payroll.models.salary_component import SalaryComponent
from payroll.models.salary_component_audit_log import SalaryComponentAuditLog
from payroll.serializers.expense_serializer import (
    ExpenseCategorySerializer, ExpenseClaimSerializer,
    ExpenseApprovalWorkflowSerializer, ExpenseStatsSerializer
)
from hr_management.models.hr_management_models import Employee
from authentication.models.user import User
from payroll.utils.company_context import get_company_from_request



class SalaryComponentListView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            # -----------------------------
            # Resolve company from request
            # -----------------------------
            employee = Employee.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()

            if not employee:
                return Response(
                    {"status": False, "message": "Employee not found"},
                    status=403
                )

            company = employee.company

            if not company:
                return Response(
                    {
                        "status": False,
                        "message": "Unauthorized"
                    },
                    status=403
                )

            # -----------------------------
            # Fetch active salary components
            # -----------------------------
            components = SalaryComponent.objects.filter(
                company=company,
                deleted_at__isnull=True
            ).order_by("name")

            records = []
            for c in components:
                records.append({
                    "id": str(c.id),
                    "name": c.name,
                    "type": c.component_type,
                    "calc_type": c.calculation_type,
                    "percentage": float(c.percentage) if c.percentage else 0,
                    "percentage_of": c.percentage_of,
                    "is_active": c.is_active,
                    "is_taxable": c.is_taxable,
                })

            return Response({
                "status": True,
                "records": records
            })

        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": "Failed to load salary components",
                    "error": str(e)
                },
                status=500
            )



class SalaryComponentCreateView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            employee = Employee.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()

            if not employee:
                return Response(
                    {"status": False, "message": "Employee not found"},
                    status=403
                )

            company = employee.company

            if not company:
                return Response(
                    {"status": False, "message": "Unauthorized"},
                    status=403
                )

            required_fields = ["name", "component_type", "calculation_type"]
            for field in required_fields:
                if field not in request.data:
                    return Response(
                        {
                            "status": False,
                            "message": f"{field} is required"
                        },
                        status=400
                    )

            component = SalaryComponent.objects.create(
                company=company,
                name=request.data["name"],
                component_type=request.data["component_type"],
                calculation_type=request.data["calculation_type"],
                percentage=request.data.get("percentage"),
                percentage_of=request.data.get("percentage_of"),
                is_taxable=request.data.get("is_taxable", True),
                is_active=True
            )

            SalaryComponentAuditLog.objects.create(
                component=component,
                action="CREATED",
                changed_by=request.user,
                snapshot={
                    "name": component.name,
                    "type": component.component_type,
                    "calc_type": component.calculation_type,
                    "percentage": component.percentage,
                    "percentage_of": component.percentage_of,
                    "is_taxable": component.is_taxable,
                    "is_active": component.is_active,
                }
            )


            return Response({
                "status": True,
                "message": "Salary component created"
            })

        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": "Failed to create salary component",
                    "error": str(e)
                },
                status=500
            )



class SalaryComponentUpdateView(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, pk):
        try:
            component = SalaryComponent.objects.get(id=pk)

            for field in [
                "name",
                "component_type",
                "calculation_type",
                "percentage",
                "percentage_of",
                "is_taxable",
            ]:
                if field in request.data:
                    setattr(component, field, request.data[field])

            component.save()

            # ✅ AUDIT LOG (POST-SAVE SNAPSHOT)
            SalaryComponentAuditLog.objects.create(
                component=component,
                action="UPDATED",
                changed_by=request.user,
                snapshot={
                    "name": component.name,
                    "component_type": component.component_type,
                    "calculation_type": component.calculation_type,
                    "percentage": float(component.percentage or 0),
                    "percentage_of": component.percentage_of,
                    "is_taxable": component.is_taxable,
                    "is_active": component.is_active,
                }
            )

            return Response({"status": True})

        except SalaryComponent.DoesNotExist:
            return Response(
                {"status": False, "message": "Component not found"},
                status=404
            )

        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": "Failed to update salary component",
                    "error": str(e)
                },
                status=500
            )




class SalaryComponentToggleView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            component_id = request.data.get("component_id")
            if not component_id:
                return Response(
                    {"status": False, "message": "component_id is required"},
                    status=400
                )

            # Resolve employee + company
            employee = Employee.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()

            if not employee or not employee.company:
                return Response(
                    {"status": False, "message": "Unauthorized"},
                    status=403
                )

            component = SalaryComponent.objects.filter(
                id=component_id,
                company=employee.company,
                deleted_at__isnull=True
            ).first()

            if not component:
                return Response(
                    {"status": False, "message": "Salary component not found"},
                    status=404
                )

            # Toggle
            component.is_active = not component.is_active
            component.save(update_fields=["is_active"])

            # Audit AFTER change
            SalaryComponentAuditLog.objects.create(
                component=component,
                action="TOGGLED",
                changed_by=request.user,
                snapshot={
                    "name": component.name,
                    "component_type": component.component_type,
                    "calculation_type": component.calculation_type,
                    "percentage": float(component.percentage or 0),
                    "percentage_of": component.percentage_of,
                    "is_taxable": component.is_taxable,
                    "is_active": component.is_active,
                }
            )

            return Response({
                "status": True,
                "records": {
                    "is_active": component.is_active
                }
            })

        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": "Failed to toggle salary component",
                    "error": str(e)
                },
                status=500
            )



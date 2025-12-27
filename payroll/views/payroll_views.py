from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q, Sum, Avg, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, date, timedelta
from decimal import Decimal

from payroll.models.payroll_models import *
from payroll.models.benefits_models import TaxConfiguration
from payroll.serializers.payroll_serializer import *
from hr_management.models.hr_management_models import Employee
from payroll.utils.challan_generator import generate_statutory_challans
from payroll.utils.form16_pdf import generate_form16_pdf
from payroll.utils.form16_utils import generate_form16_summary
from payroll.utils.payroll_lock import ensure_payroll_not_locked

from time_tracking.models.time_tracking_models import TimeEntry
from hr_management.models.hr_management_models import Employee
from payroll.models import Payroll, PayrollPeriod
from payroll.utils.payroll_calculator import calculate_employee_payroll
from django.db import transaction
from django.http import HttpResponse
from payroll.utils.payslip_pdf import generate_payslip_pdf
import pdfkit
from django.template.loader import render_to_string
from django.utils.timezone import now
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from payroll.utils.date_utils import get_financial_year


class PayrollPeriodList(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            periods = PayrollPeriod.objects.all().order_by('-start_date')
            serializer = PayrollPeriodSerializer(periods, many=True)

            return Response({
                'status': True,
                'data': serializer.data
            })

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Failed to load payroll periods',
                'error': str(e)
            }, status=500)



class PayrollPeriodAdd(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer = PayrollPeriodSerializer(data=request.data)
            if serializer.is_valid():
                period = serializer.save()
                return Response({
                    'status': True,
                    'message': 'Payroll period created successfully',
                    'records': serializer.data
                }, status=status.HTTP_200_OK)

            return Response({
                'status': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error creating payroll period',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class PayrollGenerate(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            pay_run_id = request.data.get('pay_run_id')
            if not pay_run_id:
                return Response({'status': False, 'message': 'pay_run_id is required'}, status=400)

            payrun = PayRun.objects.filter(id=pay_run_id).first()
            if not payrun:
                return Response({'status': False, 'message': 'Invalid Pay Run'}, status=404)

            if payrun.status == "FINALIZED":
                return Response({
                    "status": False,
                    "message": "Cannot regenerate payroll after finalization"
                }, status=400)

            
            if payrun.status != 'DRAFT':
                return Response({'status': False, 'message': 'Payroll already generated'}, status=400)

            current_employee = Employee.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()

            if not current_employee or not current_employee.company:
                return Response({'status': False, 'message': 'Unauthorized'}, status=403)

            employees = Employee.objects.filter(
                company=current_employee.company,
                deleted_at__isnull=True
            )

            created_count = 0

            with transaction.atomic():
                for emp in employees:
                    payroll, created = Payroll.objects.get_or_create(
                        employee=emp,
                        payroll_period=payrun.payroll_period,
                        defaults={'pay_run': payrun}
                    )

                    values = calculate_employee_payroll(emp)
                    for field, value in values.items():
                        setattr(payroll, field, value)

                    payroll.status = 'Calculated'
                    payroll.processed_by = request.user
                    payroll.save()

                    if created:
                        created_count += 1

                payrun.total_employees = employees.count()
                payrun.status = 'IN_PROGRESS'
                payrun.save(update_fields=['total_employees', 'status'])

            return Response({
                'status': True,
                'message': 'Payroll generated successfully',
                'records': {'employees_processed': created_count}
            })

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Failed to generate payroll',
                'error': str(e)
            }, status=500)



class PayrollList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            current_employee = Employee.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()

            if not current_employee or not current_employee.company:
                return Response({'status': False, 'message': 'Unauthorized'}, status=403)

            payrolls = Payroll.objects.filter(
                employee__company=current_employee.company
            ).select_related('employee', 'payroll_period', 'pay_run')

            serializer = PayrollSerializer(payrolls, many=True)

            return Response({
                'status': True,
                'records': serializer.data
            })

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Failed to load payroll list',
                'error': str(e)
            }, status=500)



class PayrollApprove(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            payroll_id = request.data.get('payroll_id')
            allowances = request.data.get('allowances', {})

            payroll = Payroll.objects.select_related(
                'employee', 'pay_run'
            ).filter(id=payroll_id).first()
            
            if payroll.pay_run.status == 'FINALIZED':
                return Response({
                    'status': False,
                    'message': 'Payroll is finalized and cannot be modified'
                }, status=400)


            if not payroll:
                return Response({'status': False, 'message': 'Payroll not found'}, status=404)

            if payroll.pay_run.status != 'IN_PROGRESS':
                return Response({
                    'status': False,
                    'message': 'Payroll is locked'
                }, status=400)

            # Update editable allowances
            payroll.house_rent_allowance = allowances.get(
                'house_rent_allowance', payroll.house_rent_allowance
            )
            payroll.transport_allowance = allowances.get(
                'transport_allowance', payroll.transport_allowance
            )
            payroll.other_allowances = allowances.get(
                'bonus', payroll.other_allowances
            )

            # Recalculate totals
            payroll.gross_salary = (
                payroll.basic_salary +
                payroll.house_rent_allowance +
                payroll.transport_allowance +
                payroll.other_allowances
            )

            payroll.total_deductions = (
                payroll.provident_fund +
                payroll.professional_tax +
                payroll.income_tax
            )

            payroll.net_salary = payroll.gross_salary - payroll.total_deductions

            payroll.save()

            return Response({
                'status': True,
                'message': 'Payroll updated successfully'
            })

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Failed to update payroll',
                'error': str(e)
            }, status=500)




class PayrollStats(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            current_employee = Employee.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()

            if not current_employee or not current_employee.company:
                return Response({'status': False, 'message': 'Unauthorized'}, status=403)

            stats = Payroll.objects.filter(
                employee__company=current_employee.company
            ).aggregate(
                total_gross=models.Sum('gross_salary'),
                total_deductions=models.Sum('total_deductions'),
                total_net=models.Sum('net_salary')
            )

            return Response({
                'status': True,
                'records': stats
            })

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Failed to load payroll stats',
                'error': str(e)
            }, status=500)




class PayrollDashboardSummary(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            current_employee = Employee.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()

            if not current_employee or not current_employee.company:
                return Response(
                    {'status': False, 'message': 'Unauthorized'},
                    status=403
                )

            company = current_employee.company

            total_employees = Employee.objects.filter(
                company=company,
                deleted_at__isnull=True
            ).count()

            total_payroll = Payroll.objects.filter(
                employee__company=company
            ).aggregate(
                total=models.Sum('net_salary')
            )['total'] or 0

            return Response({
                'status': True,
                'records': {
                    'total_employees': total_employees,
                    'monthly_payroll': total_payroll,
                    'pending_approvals': 0,
                    'next_pay_run': None
                }
            })

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Failed to load dashboard summary',
                'error': str(e)
            }, status=500)




class PayrollDashboardCharts(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            # ===== Payroll Trend (Last 6 periods) =====
            trend_qs = (
                Payroll.objects
                .filter(deleted_at__isnull=True)
                .values('payroll_period__period_name')
                .annotate(total=Sum('net_salary'))
                .order_by('-payroll_period__start_date')[:6]
            )

            trend_labels = []
            trend_data = []

            for row in reversed(trend_qs):
                trend_labels.append(row['payroll_period__period_name'])
                trend_data.append(row['total'] or 0)

            # ===== Department Cost =====
            dept_qs = (
                Payroll.objects
                .filter(deleted_at__isnull=True)
                .values('employee__department__name')
                .annotate(total=Sum('net_salary'))
            )

            dept_labels = []
            dept_data = []

            for row in dept_qs:
                dept_labels.append(row['employee__department__name'] or 'Unknown')
                dept_data.append(row['total'] or 0)

            return Response({
                'status': True,
                'records': {
                    'payrollTrend': {
                        'labels': trend_labels,
                        'data': trend_data
                    },
                    'departmentCost': {
                        'labels': dept_labels,
                        'data': dept_data
                    }
                }
            }, status=200)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Failed to load chart data',
                'error': str(e)
            }, status=400)


class PayRunListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            payruns = PayRun.objects.all()
            serializer = PayRunSerializer(payruns, many=True)

            return Response({
                'status': True,
                'data': serializer.data
            })

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Failed to load pay runs',
                'error': str(e)
            }, status=500)



class PayRunCreateView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            period_id = request.data.get('payroll_period')

            if not period_id:
                return Response({
                    'status': False,
                    'message': 'payroll_period is required'
                }, status=400)

            if PayRun.objects.filter(payroll_period_id=period_id).exists():
                return Response({
                    'status': False,
                    'message': 'Pay Run already exists for this period'
                }, status=400)

            payrun = PayRun.objects.create(
                payroll_period_id=period_id,
                created_by=request.user
            )

            return Response({
                'status': True,
                'data': PayRunSerializer(payrun).data
            })

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Failed to create pay run',
                'error': str(e)
            }, status=500)



class PayRunGeneratePayrollView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            pay_run_id = request.data.get('pay_run_id')

            if not pay_run_id:
                return Response({
                    'status': False,
                    'message': 'pay_run_id is required'
                }, status=400)

            payrun = PayRun.objects.filter(id=pay_run_id).first()
            if not payrun:
                return Response({
                    'status': False,
                    'message': 'Invalid Pay Run'
                }, status=404)
            if payrun.status == "FINALIZED":
                return Response({
                    "status": False,
                    "message": "Cannot regenerate payroll after finalization"
                }, status=400)

            if payrun.status != 'DRAFT':
                return Response({
                    'status': False,
                    'message': 'Payroll already generated'
                }, status=400)

            # 🔹 Identify HR employee & company
            current_employee = Employee.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()

            if not current_employee or not current_employee.company:
                return Response({
                    'status': False,
                    'message': 'Unauthorized'
                }, status=403)

            employees = Employee.objects.filter(
                company=current_employee.company,
                deleted_at__isnull=True
            )

            created_count = 0

            with transaction.atomic():
                for emp in employees:
                    payroll, created = Payroll.objects.get_or_create(
                        employee=emp,
                        payroll_period=payrun.payroll_period,
                        defaults={
                            'pay_run': payrun,
                            'processed_by': request.user
                        }
                    )

                    # ⚠️ Prevent duplicates
                    if not created:
                        continue

                    values = calculate_employee_payroll(emp)
                    for field, value in values.items():
                        setattr(payroll, field, value)

                    payroll.status = 'CALCULATED'
                    payroll.save()
                    created_count += 1

                payrun.total_employees = created_count
                payrun.status = 'IN_PROGRESS'
                payrun.save(update_fields=['total_employees', 'status'])

            return Response({
                'status': True,
                'message': 'Payroll generated successfully',
                'records': {
                    'employees_processed': created_count
                }
            })

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Failed to generate payroll',
                'error': str(e)
            }, status=500)



class PayRunEmployeeListView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            pay_run_id = request.data.get('pay_run_id')

            if not pay_run_id:
                return Response({'status': False, 'message': 'pay_run_id is required'}, status=400)

            current_employee = Employee.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()

            if not current_employee or not current_employee.company:
                return Response({'status': False, 'message': 'Unauthorized'}, status=403)

            payrolls = Payroll.objects.filter(
                pay_run_id=pay_run_id,
                employee__company=current_employee.company,
                deleted_at__isnull=True
            ).select_related('employee', 'employee__user')

            serializer = PayrollSerializer(payrolls, many=True)

            return Response({
                'status': True,
                'records': serializer.data
            })

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Failed to load payroll list',
                'error': str(e)
            }, status=500)



class PayRunFinalizeView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            pay_run_id = request.data.get("pay_run_id")

            payrun = PayRun.objects.get(id=pay_run_id)

            if payrun.status != "IN_PROGRESS":
                return Response({
                    "status": False,
                    "message": "Invalid payrun status"
                }, status=400)

            payrolls = Payroll.objects.filter(
                pay_run=payrun
            )

            # 🔥 AUTO CREATE CHALLANS
            generate_statutory_challans(payrun, payrolls)

            payrun.status = "FINALIZED"
            payrun.finalized_at = now()
            payrun.save()

            return Response({
                "status": True,
                "message": "PayRun finalized & challans generated"
            })

        except Exception as e:
            return Response({
                "status": False,
                "message": "Failed to finalize payrun",
                "error": str(e)
            }, status=500)
        

class PayRunSummaryView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            pay_run_id = request.data.get('pay_run_id')

            if not pay_run_id:
                return Response({
                    'status': False,
                    'message': 'pay_run_id is required'
                }, status=400)

            # 1️⃣ Logged-in employee
            current_employee = Employee.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()

            if not current_employee or not current_employee.company:
                return Response({
                    'status': False,
                    'message': 'Unauthorized'
                }, status=403)

            company = current_employee.company

            # 2️⃣ Fetch PayRun (no company join here)
            pay_run = PayRun.objects.filter(id=pay_run_id).select_related(
                'payroll_period'
            ).first()

            if not pay_run:
                return Response({
                    'status': False,
                    'message': 'Pay Run not found'
                }, status=404)

            # 3️⃣ Payroll rows scoped by company
            payroll_qs = Payroll.objects.filter(
                pay_run=pay_run,
                employee__company=company
            )

            # 4️⃣ Aggregation
            totals = payroll_qs.aggregate(
                total_gross_salary=Sum('gross_salary'),
                total_deductions=Sum('total_deductions'),
                total_net_salary=Sum('net_salary')
            )

            total_employees = payroll_qs.count()

            response_data = {
                'id': str(pay_run.id),
                'payroll_period_id': str(pay_run.payroll_period.id),
                'payroll_period_name': pay_run.payroll_period.period_name,
                'status': pay_run.status,
                'total_employees': total_employees,
                'total_gross_salary': totals['total_gross_salary'] or Decimal('0.00'),
                'total_deductions': totals['total_deductions'] or Decimal('0.00'),
                'total_net_salary': totals['total_net_salary'] or Decimal('0.00'),
                'created_at': pay_run.created_at,
                'finalized_at': pay_run.finalized_at
            }

            return Response({
                'status': True,
                'records': response_data
            })

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Failed to load Pay Run summary',
                'error': str(e)
            }, status=500)



class PayRunLockCheckView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            pay_run_id = request.data.get('pay_run_id')

            if not pay_run_id:
                return Response({
                    'status': False,
                    'locked': True,
                    'message': 'pay_run_id is required'
                }, status=400)

            pay_run = PayRun.objects.filter(id=pay_run_id).first()
            if not pay_run:
                return Response({
                    'status': False,
                    'locked': True,
                    'message': 'Pay Run not found'
                }, status=404)

            return Response({
                'status': True,
                'locked': pay_run.status in ['FINALIZED', 'POSTED']
            })

        except Exception as e:
            return Response({
                'status': False,
                'locked': True,
                'message': 'Failed to check pay run lock status',
                'error': str(e)
            }, status=500)


class PayrollDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            payroll_id = request.data.get('payroll_id')

            payroll = Payroll.objects.select_related('pay_run').filter(
                id=payroll_id,
                deleted_at__isnull=True
            ).first()

            if not payroll:
                return Response({'status': False, 'message': 'Payroll not found'}, status=404)

            return Response({
                'status': True,
                'records': {
                    'payroll': PayrollSerializer(payroll).data,
                    'pay_run_status': payroll.pay_run.status
                }
            })

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Failed to load payroll',
                'error': str(e)
            }, status=500)



class PayslipDownloadView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            payroll_id = request.data.get('payroll_id')
            payroll = Payroll.objects.select_related(
                'employee', 'employee__department', 'payroll_period'
            ).get(id=payroll_id)

            html = render_to_string(
                'payslip/payslip.html',
                {'payroll': payroll}
            )

            pdf = pdfkit.from_string(html, False)

            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = (
                f'attachment; filename="Payslip_{payroll.employee.user.first_name}.pdf"'
            )
            return response

        except Payroll.DoesNotExist:
            return Response({'status': False, 'message': 'Invalid payroll'}, status=404)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Failed to generate payslip',
                'error': str(e)
            }, status=500)




class PayslipGenerateView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            payroll_id = request.data.get("payroll_id")
            if not payroll_id:
                return Response(
                    {"status": False, "message": "payroll_id is required"},
                    status=400
                )

            payroll = Payroll.objects.select_related(
                "employee",
                "employee__company",
                "payroll_period",
                "employee__department",
                "employee__user",
            ).get(id=payroll_id)

            employee = payroll.employee
            company = employee.company

            context = {
                "company_name": company.name,
                "employee_name": employee.user.name,
                "employee_id": str(employee.id),
                "department": employee.department.name if employee.department else "-",
                "pay_period": payroll.payroll_period.start_date,
                "pay_date": now().strftime("%d %b %Y"),

                "basic_salary": payroll.basic_salary,
                "hra": payroll.house_rent_allowance,
                "transport": payroll.transport_allowance,
                "overtime": payroll.overtime_amount,
                "bonus": payroll.performance_bonus,

                "pf": payroll.provident_fund,
                "professional_tax": payroll.professional_tax,
                "income_tax": payroll.income_tax,

                "gross_salary": payroll.gross_salary,
                "total_deductions": payroll.total_deductions,
                "net_pay": payroll.net_salary,
            }

            pdf_buffer = generate_payslip_pdf(context)

            response = HttpResponse(
                pdf_buffer,
                content_type="application/pdf"
            )
            response["Content-Disposition"] = (
                f'attachment; filename="Payslip_{employee.user.name}.pdf"'
            )
            return response

        except Payroll.DoesNotExist:
            return Response(
                {"status": False, "message": "Payroll not found"},
                status=404
            )

        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": "Payslip generation failed",
                    "error": str(e)
                },
                status=500
            )
        

class EmployeePayslipListView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            user = request.user

            # 1️⃣ Resolve employee
            employee = Employee.objects.filter(
                user=user,
                deleted_at__isnull=True
            ).first()

            if not employee:
                return Response(
                    {"status": False, "message": "Employee not found"},
                    status=403
                )

            month = request.data.get("month")
            year = request.data.get("year")

            # 2️⃣ Correct FK usage: pay_run (not payrun)
            payrolls = Payroll.objects.select_related(
                "payroll_period",
                "pay_run"
            ).filter(
                employee=employee,
                pay_run__status="FINALIZED",
                deleted_at__isnull=True
            ).order_by("-payroll_period__start_date")

            if month:
                payrolls = payrolls.filter(
                    payroll_period__start_date__month=month
                )

            if year:
                payrolls = payrolls.filter(
                    payroll_period__start_date__year=year
                )

            # 3️⃣ Serialize minimal, employee-safe data
            data = []
            for p in payrolls:
                data.append({
                    "payroll_id": str(p.id),
                    "pay_period": p.payroll_period.start_date,
                    "gross_salary": p.gross_salary,
                    "total_deductions": p.total_deductions,
                    "net_salary": p.net_salary,
                    "pay_date": p.pay_run.finalized_at,
                })

            return Response({
                "status": True,
                "records": data
            })

        except Exception as e:
            return Response({
                "status": False,
                "message": "Failed to load payslips",
                "error": str(e)
            }, status=500)

        
class Form16SummaryView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            financial_year = request.data.get("financial_year")
            if not financial_year:
                return Response(
                    {"status": False, "message": "financial_year is required"},
                    status=400
                )

            employee = Employee.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()

            if not employee:
                return Response(
                    {"status": False, "message": "Employee not found"},
                    status=403
                )

            summary = generate_form16_summary(employee, financial_year)

            return Response({
                "status": True,
                "records": summary
            })

        except Exception as e:
            return Response({
                "status": False,
                "message": "Failed to load Form-16 summary",
                "error": str(e)
            }, status=500)

class Form16DownloadView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            financial_year = request.data.get("financial_year")
            if not financial_year:
                return Response(
                    {"status": False, "message": "financial_year is required"},
                    status=400
                )

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

            summary = generate_form16_summary(employee, financial_year)
            pdf = generate_form16_pdf(
                employee=employee,
                company=company,
                financial_year=financial_year,
                summary=summary
            )

            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="Form16_{financial_year}.pdf"'
            )
            return response

        except Exception as e:
            return Response({
                "status": False,
                "message": "Form-16 download failed",
                "error": str(e)
            }, status=500)


class PayrollUpdateView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        payroll_id = request.data.get("payroll_id")

        payroll = Payroll.objects.select_related("pay_run").get(id=payroll_id)

        # 🔒 HARD LOCK CHECK
        ensure_payroll_not_locked(payroll)

        payroll.overtime_hours = request.data.get("overtime_hours", payroll.overtime_hours)
        payroll.performance_bonus = request.data.get("performance_bonus", payroll.performance_bonus)

        payroll.recalculate()  # your existing salary engine
        payroll.save()

        return Response({
            "status": True,
            "message": "Payroll updated successfully"
        })

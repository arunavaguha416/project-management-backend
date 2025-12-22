# payroll/views/payroll_views.py

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
from time_tracking.models.time_tracking_models import TimeEntry
from hr_management.models.hr_management_models import Employee
from payroll.models import Payroll, PayrollPeriod
from payroll.services.payroll_calculator import calculate_employee_payroll
from django.db import transaction

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

            payrun = PayRun.objects.filter(id=pay_run_id).first()
            if not payrun:
                return Response({'status': False, 'message': 'Invalid Pay Run'}, status=404)

            current_employee = Employee.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()

            if not current_employee or not current_employee.company:
                return Response({'status': False, 'message': 'Unauthorized'}, status=403)

            payrolls = Payroll.objects.select_related('employee').filter(
                pay_run=payrun,
                employee__company=current_employee.company
            )

            serializer = PayrollSerializer(payrolls, many=True)

            return Response({
                'status': True,
                'records': serializer.data
            })

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Failed to fetch payroll employees',
                'error': str(e)
            }, status=500)


class PayRunFinalizeView(APIView):
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
            if not payrun or payrun.status != 'IN_PROGRESS':
                return Response({
                    'status': False,
                    'message': 'Pay Run not ready to finalize'
                }, status=400)

            payrolls = Payroll.objects.filter(pay_run=payrun)

            payrun.total_gross_salary = sum(p.gross_salary for p in payrolls)
            payrun.total_deductions = sum(p.total_deductions for p in payrolls)
            payrun.total_net_salary = sum(p.net_salary for p in payrolls)

            payrun.status = 'FINALIZED'
            payrun.finalized_by = request.user
            payrun.finalized_at = timezone.now()
            payrun.save()

            payrolls.update(
                status='Approved',
                approved_by=request.user
            )


            return Response({
                'status': True,
                'message': 'Pay Run finalized successfully'
            })

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Failed to finalize pay run',
                'error': str(e)
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




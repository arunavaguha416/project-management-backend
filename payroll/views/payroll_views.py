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

from payroll.models.payroll_models import PayrollPeriod, Payroll, PerformanceMetric
from payroll.models.benefits_models import TaxConfiguration
from payroll.serializers.payroll_serializer import (
    PayrollPeriodSerializer, PayrollSerializer, PerformanceMetricSerializer, PayrollSummarySerializer
)
from hr_management.models.hr_management_models import Employee
from time_tracking.models.time_tracking_models import TimeEntry


class PayrollPeriodList(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            search_data = request.data
            page = int(search_data.get('page', 1))
            page_size = int(search_data.get('page_size', 10))
            status_filter = search_data.get('status', '')

            query = Q()
            if status_filter:
                query &= Q(status=status_filter)

            periods = PayrollPeriod.objects.filter(query).order_by('-start_date')

            if periods.exists():
                paginator = Paginator(periods, page_size)
                try:
                    paginated_periods = paginator.page(page)
                except:
                    paginated_periods = paginator.page(1)

                serializer = PayrollPeriodSerializer(paginated_periods, many=True)
                return Response({
                    'status': True,
                    'count': paginator.count,
                    'num_pages': paginator.num_pages,
                    'current_page': page,
                    'records': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'No payroll periods found',
                    'count': 0,
                    'records': []
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching payroll periods',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


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
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            period_id = request.data.get('period_id')
            employee_ids = request.data.get('employee_ids', [])

            period = PayrollPeriod.objects.filter(id=period_id).first()
            if not period:
                return Response({
                    'status': False,
                    'message': 'Payroll period not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Get employees to process
            if employee_ids:
                employees = Employee.objects.filter(id__in=employee_ids)
            else:
                employees = Employee.objects.filter(user__is_active=True)

            generated_count = 0
            errors = []

            for employee in employees:
                try:
                    # Check if payroll already exists
                    existing_payroll = Payroll.objects.filter(
                        employee=employee,
                        payroll_period=period
                    ).first()

                    if existing_payroll:
                        continue

                    # Calculate overtime from time tracking
                    overtime_hours = self.calculate_overtime_hours(employee, period)

                    # Get performance metrics
                    performance_metric = PerformanceMetric.objects.filter(
                        employee=employee,
                        period=period
                    ).first()

                    # Calculate bonuses based on performance
                    performance_bonus = 0
                    attendance_bonus = 0

                    if performance_metric:
                        base_bonus = employee.basic_salary * Decimal('0.1') if employee.basic_salary else 0  # 10% base bonus
                        performance_bonus = base_bonus * performance_metric.bonus_multiplier

                        # Attendance bonus if > 95% attendance
                        if performance_metric.attendance_percentage > 95:
                            attendance_bonus = employee.basic_salary * Decimal('0.05') if employee.basic_salary else 0

                    # Calculate tax deductions
                    tax_deductions = self.calculate_tax_deductions(employee)

                    # Create payroll record
                    payroll = Payroll.objects.create(
                        employee=employee,
                        payroll_period=period,
                        basic_salary=employee.basic_salary or 0,
                        overtime_hours=overtime_hours,
                        house_rent_allowance=employee.basic_salary * Decimal('0.4') if employee.basic_salary else 0,
                        transport_allowance=Decimal('2000'),
                        medical_allowance=Decimal('1500'),
                        performance_bonus=performance_bonus,
                        attendance_bonus=attendance_bonus,
                        provident_fund=employee.basic_salary * Decimal('0.12') if employee.basic_salary else 0,
                        professional_tax=tax_deductions.get('professional_tax', 0),
                        income_tax=tax_deductions.get('income_tax', 0),
                        processed_by=request.user,
                        status='Calculated'
                    )

                    generated_count += 1

                except Exception as e:
                    errors.append(f"Error processing {employee.user.name}: {str(e)}")

            return Response({
                'status': True,
                'message': f'Payroll generated for {generated_count} employees',
                'records': {
                    'generated_count': generated_count,
                    'errors': errors
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error generating payroll',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def calculate_overtime_hours(self, employee, period):
        """Calculate overtime hours from time tracking"""
        try:
            time_entries = TimeEntry.objects.filter(
                user=employee.user,
                date__range=[period.start_date, period.end_date],
                duration__isnull=False
            )

            total_hours = sum([
                entry.duration.total_seconds() / 3600
                for entry in time_entries
            ])

            # Standard working hours per month (22 working days * 8 hours)
            standard_hours = 176
            return max(0, total_hours - standard_hours)

        except:
            return 0

    def calculate_tax_deductions(self, employee):
        """Calculate tax deductions based on tax configuration"""
        try:
            tax_config = TaxConfiguration.objects.filter(
                is_active=True,
                country='India'
            ).first()

            if not tax_config:
                return {'professional_tax': 0, 'income_tax': 0}

            annual_salary = (employee.basic_salary or 0) * 12

            # Professional Tax
            professional_tax = (employee.basic_salary or 0) * tax_config.professional_tax_rate / 100

            # Income Tax (simplified calculation)
            income_tax = 0
            if annual_salary > 500000:  # Above 5 lakhs
                taxable_income = annual_salary - tax_config.standard_deduction
                for slab in tax_config.tax_slabs:
                    if taxable_income > slab['min']:
                        taxable_amount = min(taxable_income, slab['max']) - slab['min']
                        income_tax += taxable_amount * slab['rate'] / 100

                income_tax = income_tax / 12  # Monthly tax

            return {
                'professional_tax': round(professional_tax, 2),
                'income_tax': round(income_tax, 2)
            }

        except:
            return {'professional_tax': 0, 'income_tax': 0}


class PayrollList(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            search_data = request.data
            page = int(search_data.get('page', 1))
            page_size = int(search_data.get('page_size', 10))
            period_id = search_data.get('period_id')
            employee_id = search_data.get('employee_id')
            status_filter = search_data.get('status', '')

            # Base query - HR and ADMIN can see all, others see only their own
            if request.user.role in ['HR', 'ADMIN','MANAGER']:
                query = Q()
            else:
                # Employees see their own payroll
                employee = Employee.objects.filter(user=request.user).first()
                if not employee:
                    return Response({
                        'status': False,
                        'message': 'Employee record not found',
                        'records': []
                    }, status=status.HTTP_200_OK)
                query = Q(employee=employee)

            # Apply filters
            if period_id:
                query &= Q(payroll_period_id=period_id)
            if employee_id and request.user.role in ['HR', 'ADMIN']:
                query &= Q(employee_id=employee_id)
            if status_filter:
                query &= Q(status=status_filter)

            payrolls = Payroll.objects.filter(query).select_related(
                'employee__user', 'payroll_period', 'processed_by', 'approved_by'
            ).order_by('-created_at')

            if payrolls.exists():
                paginator = Paginator(payrolls, page_size)
                try:
                    paginated_payrolls = paginator.page(page)
                except:
                    paginated_payrolls = paginator.page(1)

                serializer = PayrollSerializer(paginated_payrolls, many=True)
                return Response({
                    'status': True,
                    'count': paginator.count,
                    'num_pages': paginator.num_pages,
                    'current_page': page,
                    'records': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'No payroll records found',
                    'count': 0,
                    'records': []
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching payroll records',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class PayrollApprove(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Only HR and ADMIN can approve payroll
            if request.user.role not in ['HR', 'ADMIN']:
                return Response({
                    'status': False,
                    'message': 'Insufficient permissions'
                }, status=status.HTTP_403_FORBIDDEN)

            payroll_ids = request.data.get('payroll_ids', [])
            action = request.data.get('action', 'approve')  # approve/reject

            if not payroll_ids:
                return Response({
                    'status': False,
                    'message': 'No payroll IDs provided'
                }, status=status.HTTP_400_BAD_REQUEST)

            payrolls = Payroll.objects.filter(id__in=payroll_ids)
            updated_count = 0

            for payroll in payrolls:
                if action == 'approve':
                    payroll.status = 'Approved'
                    payroll.approved_by = request.user
                elif action == 'reject':
                    payroll.status = 'Draft'
                    payroll.approved_by = None

                payroll.save()
                updated_count += 1

            return Response({
                'status': True,
                'message': f'{updated_count} payroll records {action}d successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': f'Error {action}ing payroll records',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class PayrollStats(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            period_id = request.data.get('period_id')
            if not period_id:
                return Response({
                    'status': False,
                    'message': 'Period ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get payroll statistics for the period
            payrolls = Payroll.objects.filter(payroll_period_id=period_id)

            if not payrolls.exists():
                return Response({
                    'status': False,
                    'message': 'No payroll data found for this period',
                    'records': {}
                }, status=status.HTTP_200_OK)

            # Calculate statistics
            stats = payrolls.aggregate(
                total_employees=Count('id'),
                total_gross_salary=Sum('gross_salary'),
                total_deductions=Sum('total_deductions'),
                total_net_salary=Sum('net_salary'),
                total_overtime_amount=Sum('overtime_amount'),
                total_bonuses=Sum('performance_bonus') + Sum('attendance_bonus') + Sum('project_bonus')
            )

            # Handle None values
            for key, value in stats.items():
                if value is None:
                    stats[key] = 0

            # Add default average_attendance to satisfy serializer
            stats['average_attendance'] = 0

            serializer = PayrollSummarySerializer(stats)
            return Response({
                'status': True,
                'records': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching payroll statistics',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)




class PerformanceMetricList(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            search_data = request.data
            page = int(search_data.get('page', 1))
            page_size = int(search_data.get('page_size', 10))
            period_id = search_data.get('period_id')

            # Base query - HR and ADMIN can see all, others see only their own
            if request.user.role in ['HR', 'ADMIN']:
                query = Q()
            else:
                employee = Employee.objects.filter(user=request.user).first()
                if not employee:
                    return Response({
                        'status': False,
                        'message': 'Employee record not found',
                        'records': []
                    }, status=status.HTTP_200_OK)
                query = Q(employee=employee)

            if period_id:
                query &= Q(period_id=period_id)

            metrics = PerformanceMetric.objects.filter(query).select_related(
                'employee__user', 'period'
            ).order_by('-created_at')

            if metrics.exists():
                paginator = Paginator(metrics, page_size)
                try:
                    paginated_metrics = paginator.page(page)
                except:
                    paginated_metrics = paginator.page(1)

                serializer = PerformanceMetricSerializer(paginated_metrics, many=True)
                return Response({
                    'status': True,
                    'count': paginator.count,
                    'num_pages': paginator.num_pages,
                    'current_page': page,
                    'records': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'No performance metrics found',
                    'count': 0,
                    'records': []
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching performance metrics',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class PerformanceMetricAdd(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Only HR and ADMIN can add/update performance metrics
            if request.user.role not in ['HR', 'ADMIN']:
                return Response({
                    'status': False,
                    'message': 'Insufficient permissions'
                }, status=status.HTTP_403_FORBIDDEN)

            serializer = PerformanceMetricSerializer(data=request.data)
            if serializer.is_valid():
                metric = serializer.save()
                return Response({
                    'status': True,
                    'message': 'Performance metric added successfully',
                    'records': PerformanceMetricSerializer(metric).data
                }, status=status.HTTP_200_OK)

            return Response({
                'status': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error adding performance metric',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

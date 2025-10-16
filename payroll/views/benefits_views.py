# payroll/views/benefits_views.py

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, date, timedelta
from decimal import Decimal

from payroll.models.benefits_models import BenefitPlan, BenefitEnrollment, TaxConfiguration
from payroll.serializers.benefits_serializer import (
    BenefitPlanSerializer, BenefitEnrollmentSerializer, TaxConfigurationSerializer
)
from hr_management.models.hr_management_models import Employee
from authentication.models.user import User


class BenefitPlanList(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            search_data = request.data
            page = int(search_data.get('page', 1))
            page_size = int(search_data.get('page_size', 10))
            plan_type = search_data.get('plan_type', '')
            is_active = search_data.get('is_active')
            search_name = search_data.get('name', '')

            query = Q()
            if plan_type:
                query &= Q(plan_type=plan_type)
            if is_active is not None:
                query &= Q(is_active=is_active)
            if search_name:
                query &= Q(name__icontains=search_name)

            plans = BenefitPlan.objects.filter(query).order_by('name')

            if plans.exists():
                paginator = Paginator(plans, page_size)
                try:
                    paginated_plans = paginator.page(page)
                except:
                    paginated_plans = paginator.page(1)

                serializer = BenefitPlanSerializer(paginated_plans, many=True, context={'request': request})
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
                    'message': 'No benefit plans found',
                    'count': 0,
                    'records': []
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching benefit plans',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BenefitPlanAdd(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            serializer = BenefitPlanSerializer(data=request.data)
            if serializer.is_valid():
                plan = serializer.save()
                return Response({
                    'status': True,
                    'message': 'Benefit plan added successfully',
                    'records': BenefitPlanSerializer(plan, context={'request': request}).data
                }, status=status.HTTP_200_OK)

            return Response({
                'status': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error adding benefit plan',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BenefitPlanDetails(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            plan_id = request.data.get('plan_id')
            if not plan_id:
                return Response({
                    'status': False,
                    'message': 'Plan ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            plan = BenefitPlan.objects.filter(id=plan_id).first()
            if not plan:
                return Response({
                    'status': False,
                    'message': 'Benefit plan not found'
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = BenefitPlanSerializer(plan, context={'request': request})
            return Response({
                'status': True,
                'records': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching benefit plan details',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BenefitPlanUpdate(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            plan_id = request.data.get('id')
            plan = BenefitPlan.objects.filter(id=plan_id).first()

            if not plan:
                return Response({
                    'status': False,
                    'message': 'Benefit plan not found'
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = BenefitPlanSerializer(plan, data=request.data, partial=True)
            if serializer.is_valid():
                updated_plan = serializer.save()
                return Response({
                    'status': True,
                    'message': 'Benefit plan updated successfully',
                    'records': BenefitPlanSerializer(updated_plan, context={'request': request}).data
                }, status=status.HTTP_200_OK)

            return Response({
                'status': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error updating benefit plan',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BenefitPlanDelete(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            plan_id = request.data.get('plan_id')
            if not plan_id:
                return Response({
                    'status': False,
                    'message': 'Plan ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            plan = BenefitPlan.objects.filter(id=plan_id).first()
            if not plan:
                return Response({
                    'status': False,
                    'message': 'Benefit plan not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Check if plan has active enrollments
            active_enrollments = BenefitEnrollment.objects.filter(
                benefit_plan=plan,
                status='Active'
            ).count()

            if active_enrollments > 0:
                return Response({
                    'status': False,
                    'message': f'Cannot delete plan with {active_enrollments} active enrollments'
                }, status=status.HTTP_400_BAD_REQUEST)

            plan.soft_delete()
            return Response({
                'status': True,
                'message': 'Benefit plan deleted successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error deleting benefit plan',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BenefitEnrollmentList(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            search_data = request.data
            page = int(search_data.get('page', 1))
            page_size = int(search_data.get('page_size', 10))
            employee_id = search_data.get('employee_id')
            plan_id = search_data.get('plan_id')
            enrollment_status = search_data.get('status', '')

            # Base query - employees see their own enrollments
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

            # Apply filters
            if employee_id and request.user.role in ['HR', 'ADMIN']:
                query &= Q(employee_id=employee_id)
            if plan_id:
                query &= Q(benefit_plan_id=plan_id)
            if enrollment_status:
                query &= Q(status=enrollment_status)

            enrollments = BenefitEnrollment.objects.filter(query).select_related(
                'employee__user', 'benefit_plan', 'submitted_by', 'approved_by'
            ).order_by('-created_at')

            if enrollments.exists():
                paginator = Paginator(enrollments, page_size)
                try:
                    paginated_enrollments = paginator.page(page)
                except:
                    paginated_enrollments = paginator.page(1)

                serializer = BenefitEnrollmentSerializer(paginated_enrollments, many=True, context={'request': request})
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
                    'message': 'No benefit enrollments found',
                    'count': 0,
                    'records': []
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching benefit enrollments',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BenefitEnrollmentAdd(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Get employee record
            employee = Employee.objects.filter(user=request.user).first()
            if not employee:
                return Response({
                    'status': False,
                    'message': 'Employee record not found'
                }, status=status.HTTP_404_NOT_FOUND)

            plan_id = request.data.get('benefit_plan')
            plan = BenefitPlan.objects.filter(id=plan_id).first()
            if not plan:
                return Response({
                    'status': False,
                    'message': 'Benefit plan not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Check if enrollment period is open
            today = date.today()
            if not (plan.enrollment_start_date <= today <= plan.enrollment_end_date):
                return Response({
                    'status': False,
                    'message': 'Enrollment period is not open for this plan'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if already enrolled
            existing_enrollment = BenefitEnrollment.objects.filter(
                employee=employee,
                benefit_plan=plan,
                status__in=['Pending', 'Active']
            ).first()

            if existing_enrollment:
                return Response({
                    'status': False,
                    'message': 'Already enrolled in this benefit plan'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Add employee and submitted_by to data
            data = request.data.copy()
            data['employee'] = employee.id
            data['submitted_by'] = request.user.id

            # Calculate costs based on coverage level
            coverage_level = data.get('coverage_level', 'Employee Only')
            employee_cost = plan.employee_contribution
            employer_cost = plan.employer_contribution

            # Adjust costs based on coverage level
            multipliers = {
                'Employee Only': 1.0,
                'Employee + Spouse': 1.8,
                'Employee + Children': 1.6,
                'Family': 2.2
            }

            multiplier = multipliers.get(coverage_level, 1.0)
            data['employee_monthly_cost'] = float(employee_cost * Decimal(str(multiplier)))
            data['employer_monthly_cost'] = float(employer_cost * Decimal(str(multiplier)))

            serializer = BenefitEnrollmentSerializer(data=data)
            if serializer.is_valid():
                enrollment = serializer.save()
                return Response({
                    'status': True,
                    'message': 'Benefit enrollment submitted successfully',
                    'records': BenefitEnrollmentSerializer(enrollment, context={'request': request}).data
                }, status=status.HTTP_200_OK)

            return Response({
                'status': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error submitting benefit enrollment',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BenefitEnrollmentUpdate(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            enrollment_id = request.data.get('id')
            enrollment = BenefitEnrollment.objects.filter(id=enrollment_id).first()

            if not enrollment:
                return Response({
                    'status': False,
                    'message': 'Benefit enrollment not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Check permissions
            if request.user.role not in ['HR', 'ADMIN'] and enrollment.employee.user != request.user:
                return Response({
                    'status': False,
                    'message': 'Insufficient permissions'
                }, status=status.HTTP_403_FORBIDDEN)

            # Only allow updates for Pending enrollments
            if enrollment.status not in ['Pending']:
                return Response({
                    'status': False,
                    'message': 'Cannot update approved enrollments'
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer = BenefitEnrollmentSerializer(enrollment, data=request.data, partial=True)
            if serializer.is_valid():
                updated_enrollment = serializer.save()
                return Response({
                    'status': True,
                    'message': 'Benefit enrollment updated successfully',
                    'records': BenefitEnrollmentSerializer(updated_enrollment, context={'request': request}).data
                }, status=status.HTTP_200_OK)

            return Response({
                'status': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error updating benefit enrollment',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BenefitEnrollmentApprove(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Only HR and ADMIN can approve enrollments
            if request.user.role not in ['HR', 'ADMIN']:
                return Response({
                    'status': False,
                    'message': 'Insufficient permissions'
                }, status=status.HTTP_403_FORBIDDEN)

            enrollment_ids = request.data.get('enrollment_ids', [])
            action = request.data.get('action', 'approve')  # approve/reject

            if not enrollment_ids:
                return Response({
                    'status': False,
                    'message': 'No enrollment IDs provided'
                }, status=status.HTTP_400_BAD_REQUEST)

            enrollments = BenefitEnrollment.objects.filter(id__in=enrollment_ids)
            updated_count = 0

            for enrollment in enrollments:
                if action == 'approve':
                    enrollment.status = 'Active'
                    enrollment.effective_date = enrollment.benefit_plan.plan_year_start
                    enrollment.end_date = enrollment.benefit_plan.plan_year_end
                elif action == 'reject':
                    enrollment.status = 'Terminated'

                enrollment.approved_by = request.user
                enrollment.approved_at = timezone.now()
                enrollment.save()
                updated_count += 1

            return Response({
                'status': True,
                'message': f'{updated_count} benefit enrollments {action}d successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': f'Error {action}ing benefit enrollments',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BenefitEnrollmentCancel(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            enrollment_id = request.data.get('enrollment_id')
            enrollment = BenefitEnrollment.objects.filter(id=enrollment_id).first()

            if not enrollment:
                return Response({
                    'status': False,
                    'message': 'Benefit enrollment not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Check permissions
            if enrollment.employee.user != request.user and request.user.role not in ['HR', 'ADMIN']:
                return Response({
                    'status': False,
                    'message': 'Insufficient permissions'
                }, status=status.HTTP_403_FORBIDDEN)

            enrollment.status = 'Terminated'
            enrollment.end_date = date.today()
            enrollment.save()

            return Response({
                'status': True,
                'message': 'Benefit enrollment cancelled successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error cancelling benefit enrollment',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BenefitEnrollmentDelete(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            enrollment_id = request.data.get('enrollment_id')
            if not enrollment_id:
                return Response({
                    'status': False,
                    'message': 'Enrollment ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            enrollment = BenefitEnrollment.objects.filter(id=enrollment_id).first()
            if not enrollment:
                return Response({
                    'status': False,
                    'message': 'Benefit enrollment not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Only allow deletion of Pending enrollments
            if enrollment.status not in ['Pending']:
                return Response({
                    'status': False,
                    'message': 'Cannot delete active enrollments'
                }, status=status.HTTP_400_BAD_REQUEST)

            enrollment.soft_delete()
            return Response({
                'status': True,
                'message': 'Benefit enrollment deleted successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error deleting benefit enrollment',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BenefitsStats(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Base query based on role
            if request.user.role in ['HR', 'ADMIN']:
                enrollment_query = Q()
                plan_query = Q()
            else:
                employee = Employee.objects.filter(user=request.user).first()
                if not employee:
                    return Response({
                        'status': False,
                        'message': 'Employee record not found',
                        'records': {}
                    }, status=status.HTTP_200_OK)
                enrollment_query = Q(employee=employee)
                plan_query = Q(is_active=True)

            # Calculate enrollment statistics
            enrollment_stats = BenefitEnrollment.objects.filter(enrollment_query).aggregate(
                total_enrollments=Count('id'),
                active_enrollments=Count('id', filter=Q(status='Active')),
                pending_enrollments=Count('id', filter=Q(status='Pending')),
                total_employee_cost=Sum('employee_monthly_cost'),
                total_employer_cost=Sum('employer_monthly_cost')
            )

            # Calculate plan statistics
            plan_stats = BenefitPlan.objects.filter(plan_query).aggregate(
                total_plans=Count('id'),
                active_plans=Count('id', filter=Q(is_active=True)),
                health_plans=Count('id', filter=Q(plan_type='Health Insurance')),
                dental_plans=Count('id', filter=Q(plan_type='Dental')),
                vision_plans=Count('id', filter=Q(plan_type='Vision')),
                retirement_plans=Count('id', filter=Q(plan_type='Retirement'))
            )

            # Enrollment by plan type
            enrollment_by_type = BenefitEnrollment.objects.filter(
                enrollment_query, status='Active'
            ).values('benefit_plan__plan_type').annotate(
                count=Count('id'),
                total_cost=Sum('employee_monthly_cost')
            ).order_by('benefit_plan__plan_type')

            # Handle None values
            for key, value in enrollment_stats.items():
                if value is None:
                    enrollment_stats[key] = 0

            for key, value in plan_stats.items():
                if value is None:
                    plan_stats[key] = 0

            stats_data = {
                **enrollment_stats,
                **plan_stats,
                'enrollment_by_type': list(enrollment_by_type),
                'annual_employee_cost': (enrollment_stats['total_employee_cost'] or 0) * 12,
                'annual_employer_cost': (enrollment_stats['total_employer_cost'] or 0) * 12
            }

            return Response({
                'status': True,
                'records': stats_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching benefits statistics',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class TaxConfigurationList(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            search_data = request.data
            page = int(search_data.get('page', 1))
            page_size = int(search_data.get('page_size', 10))
            country = search_data.get('country', '')
            is_active = search_data.get('is_active')

            query = Q()
            if country:
                query &= Q(country__icontains=country)
            if is_active is not None:
                query &= Q(is_active=is_active)

            configs = TaxConfiguration.objects.filter(query).order_by('-is_active', 'country', 'tax_year')

            if configs.exists():
                paginator = Paginator(configs, page_size)
                try:
                    paginated_configs = paginator.page(page)
                except:
                    paginated_configs = paginator.page(1)

                serializer = TaxConfigurationSerializer(paginated_configs, many=True)
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
                    'message': 'No tax configurations found',
                    'count': 0,
                    'records': []
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching tax configurations',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class TaxConfigurationAdd(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            serializer = TaxConfigurationSerializer(data=request.data)
            if serializer.is_valid():
                config = serializer.save()
                return Response({
                    'status': True,
                    'message': 'Tax configuration added successfully',
                    'records': TaxConfigurationSerializer(config).data
                }, status=status.HTTP_200_OK)

            return Response({
                'status': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error adding tax configuration',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class TaxConfigurationUpdate(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            config_id = request.data.get('id')
            config = TaxConfiguration.objects.filter(id=config_id).first()

            if not config:
                return Response({
                    'status': False,
                    'message': 'Tax configuration not found'
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = TaxConfigurationSerializer(config, data=request.data, partial=True)
            if serializer.is_valid():
                updated_config = serializer.save()
                return Response({
                    'status': True,
                    'message': 'Tax configuration updated successfully',
                    'records': TaxConfigurationSerializer(updated_config).data
                }, status=status.HTTP_200_OK)

            return Response({
                'status': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error updating tax configuration',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class TaxConfigurationActivate(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            config_id = request.data.get('config_id')
            config = TaxConfiguration.objects.filter(id=config_id).first()

            if not config:
                return Response({
                    'status': False,
                    'message': 'Tax configuration not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Deactivate other configs for the same country
            TaxConfiguration.objects.filter(
                country=config.country
            ).update(is_active=False)

            # Activate this config
            config.is_active = True
            config.save()

            return Response({
                'status': True,
                'message': 'Tax configuration activated successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error activating tax configuration',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class TaxConfigurationDelete(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            config_id = request.data.get('config_id')
            if not config_id:
                return Response({
                    'status': False,
                    'message': 'Config ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            config = TaxConfiguration.objects.filter(id=config_id).first()
            if not config:
                return Response({
                    'status': False,
                    'message': 'Tax configuration not found'
                }, status=status.HTTP_404_NOT_FOUND)

            if config.is_active:
                return Response({
                    'status': False,
                    'message': 'Cannot delete active tax configuration'
                }, status=status.HTTP_400_BAD_REQUEST)

            config.soft_delete()
            return Response({
                'status': True,
                'message': 'Tax configuration deleted successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error deleting tax configuration',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class TaxCalculator(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            annual_salary = Decimal(str(request.data.get('annual_salary', 0)))
            country = request.data.get('country', 'India')

            # Get active tax configuration
            tax_config = TaxConfiguration.objects.filter(
                country=country,
                is_active=True
            ).first()

            if not tax_config:
                return Response({
                    'status': False,
                    'message': f'No active tax configuration found for {country}'
                }, status=status.HTTP_404_NOT_FOUND)

            # Calculate income tax
            taxable_income = annual_salary - tax_config.standard_deduction
            income_tax = Decimal('0')

            for slab in tax_config.tax_slabs:
                slab_min = Decimal(str(slab['min']))
                slab_max = Decimal(str(slab['max']))
                slab_rate = Decimal(str(slab['rate']))

                if taxable_income > slab_min:
                    taxable_amount = min(taxable_income, slab_max) - slab_min
                    if taxable_amount > 0:
                        income_tax += taxable_amount * slab_rate / 100

            # Calculate other taxes
            professional_tax = annual_salary * tax_config.professional_tax_rate / 100
            provident_fund = annual_salary * tax_config.provident_fund_rate / 100

            # Calculate cess
            cess = income_tax * tax_config.cess_rate / 100

            # Calculate surcharge if applicable
            surcharge = Decimal('0')
            if annual_salary > tax_config.surcharge_threshold:
                surcharge = income_tax * tax_config.surcharge_rate / 100

            total_tax = income_tax + professional_tax + provident_fund + cess + surcharge
            net_salary = annual_salary - total_tax

            tax_breakdown = {
                'annual_salary': float(annual_salary),
                'taxable_income': float(taxable_income),
                'income_tax': float(income_tax),
                'professional_tax': float(professional_tax),
                'provident_fund': float(provident_fund),
                'cess': float(cess),
                'surcharge': float(surcharge),
                'total_tax': float(total_tax),
                'net_salary': float(net_salary),
                'effective_tax_rate': float((total_tax / annual_salary) * 100) if annual_salary > 0 else 0,
                'monthly_net_salary': float(net_salary / 12),
                'monthly_tax': float(total_tax / 12)
            }

            return Response({
                'status': True,
                'records': tax_breakdown
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error calculating tax',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BenefitsExport(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            export_type = request.data.get('export_type', 'enrollments')  # enrollments/plans
            export_format = request.data.get('format', 'csv')

            if export_type == 'enrollments':
                # Base query
                if request.user.role in ['HR', 'ADMIN']:
                    query = Q()
                else:
                    employee = Employee.objects.filter(user=request.user).first()
                    if not employee:
                        return Response({
                            'status': False,
                            'message': 'Employee record not found'
                        }, status=status.HTTP_404_NOT_FOUND)
                    query = Q(employee=employee)

                enrollments = BenefitEnrollment.objects.filter(query).select_related(
                    'employee__user', 'benefit_plan'
                ).order_by('-created_at')

                export_data = []
                for enrollment in enrollments:
                    export_data.append({
                        'employee_name': enrollment.employee.user.name,
                        'employee_email': enrollment.employee.user.email,
                        'plan_name': enrollment.benefit_plan.name,
                        'plan_type': enrollment.benefit_plan.plan_type,
                        'coverage_level': enrollment.coverage_level,
                        'employee_monthly_cost': str(enrollment.employee_monthly_cost),
                        'employer_monthly_cost': str(enrollment.employer_monthly_cost),
                        'status': enrollment.status,
                        'enrollment_date': enrollment.enrollment_date.strftime('%Y-%m-%d'),
                        'effective_date': enrollment.effective_date.strftime('%Y-%m-%d') if enrollment.effective_date else '',
                        'end_date': enrollment.end_date.strftime('%Y-%m-%d') if enrollment.end_date else ''
                    })

            else:  # plans
                if request.user.role not in ['HR', 'ADMIN']:
                    return Response({
                        'status': False,
                        'message': 'Insufficient permissions'
                    }, status=status.HTTP_403_FORBIDDEN)

                plans = BenefitPlan.objects.all().order_by('name')
                export_data = []

                for plan in plans:
                    export_data.append({
                        'name': plan.name,
                        'plan_type': plan.plan_type,
                        'provider': plan.provider,
                        'employee_contribution': str(plan.employee_contribution),
                        'employer_contribution': str(plan.employer_contribution),
                        'coverage_amount': str(plan.coverage_amount or 0),
                        'is_mandatory': plan.is_mandatory,
                        'is_active': plan.is_active,
                        'enrollment_start_date': plan.enrollment_start_date.strftime('%Y-%m-%d'),
                        'enrollment_end_date': plan.enrollment_end_date.strftime('%Y-%m-%d'),
                        'plan_year_start': plan.plan_year_start.strftime('%Y-%m-%d'),
                        'plan_year_end': plan.plan_year_end.strftime('%Y-%m-%d')
                    })

            return Response({
                'status': True,
                'message': f'Exported {len(export_data)} {export_type} records',
                'records': export_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error exporting benefits data',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

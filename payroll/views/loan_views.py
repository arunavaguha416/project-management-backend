from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from payroll.models.loan_models import LoanAdvance
from payroll.serializers.loan_serializer import LoanAdvanceSerializer
from hr_management.models.hr_management_models import Employee


class LoanAdvanceList(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            search_data = request.data
            page = int(search_data.get('page', 1))
            page_size = int(search_data.get('page_size', 10))
            loan_type = search_data.get('loan_type', '')
            status_filter = search_data.get('status', '')
            search_name = search_data.get('name', '')

            current_employee = Employee.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()

            if not current_employee:
                return Response({
                    'status': False,
                    'message': 'Employee record not found',
                    'count': 0,
                    'records': []
                }, status=status.HTTP_200_OK)

            query = Q(employee__company=current_employee.company, deleted_at__isnull=True)
            if request.user.role not in ['HR', 'ADMIN']:
                query &= Q(employee=current_employee)

            if loan_type:
                query &= Q(loan_type=loan_type)
            if status_filter:
                query &= Q(status=status_filter)
            if search_name:
                query &= Q(employee__user__name__icontains=search_name)

            loans = LoanAdvance.objects.filter(query).select_related('employee__user').order_by('-created_at')

            paginator = Paginator(loans, page_size)
            try:
                paginated_loans = paginator.page(page)
            except Exception:
                paginated_loans = paginator.page(1)

            serializer = LoanAdvanceSerializer(paginated_loans, many=True)
            return Response({
                'status': True,
                'count': paginator.count,
                'num_pages': paginator.num_pages,
                'current_page': page,
                'records': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching loans',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class LoanAdvanceAdd(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            current_employee = Employee.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()
            if not current_employee:
                return Response({
                    'status': False,
                    'message': 'Employee record not found'
                }, status=status.HTTP_404_NOT_FOUND)

            data = request.data.copy()
            if request.user.role not in ['HR', 'ADMIN']:
                data['employee'] = str(current_employee.id)
            elif not data.get('employee'):
                return Response({
                    'status': False,
                    'message': 'employee is required for HR/Admin users'
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                target_employee = Employee.objects.filter(
                    id=data.get('employee'),
                    company=current_employee.company,
                    deleted_at__isnull=True
                ).first()
                if not target_employee:
                    return Response({
                        'status': False,
                        'message': 'Invalid employee selected'
                    }, status=status.HTTP_400_BAD_REQUEST)

            serializer = LoanAdvanceSerializer(data=data)
            if serializer.is_valid():
                loan = serializer.save()
                if loan.outstanding_balance is None:
                    loan.outstanding_balance = loan.principal_amount
                    loan.save(update_fields=['outstanding_balance'])
                return Response({
                    'status': True,
                    'message': 'Loan/advance created successfully',
                    'records': LoanAdvanceSerializer(loan).data
                }, status=status.HTTP_200_OK)

            return Response({
                'status': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error creating loan/advance',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class LoanAdvanceUpdate(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            if request.user.role not in ['HR', 'ADMIN']:
                return Response({
                    'status': False,
                    'message': 'Insufficient permissions'
                }, status=status.HTTP_403_FORBIDDEN)

            current_employee = Employee.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()
            if not current_employee:
                return Response({
                    'status': False,
                    'message': 'Employee record not found'
                }, status=status.HTTP_404_NOT_FOUND)

            loan_id = request.data.get('id')
            loan = LoanAdvance.objects.filter(
                id=loan_id,
                employee__company=current_employee.company,
                deleted_at__isnull=True
            ).first()

            if not loan:
                return Response({
                    'status': False,
                    'message': 'Loan/advance not found'
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = LoanAdvanceSerializer(loan, data=request.data, partial=True)
            if serializer.is_valid():
                updated_loan = serializer.save()
                return Response({
                    'status': True,
                    'message': 'Loan/advance updated successfully',
                    'records': LoanAdvanceSerializer(updated_loan).data
                }, status=status.HTTP_200_OK)

            return Response({
                'status': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error updating loan/advance',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class LoanAdvanceEmployeeOptions(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            current_employee = Employee.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()

            if not current_employee:
                return Response({
                    'status': False,
                    'message': 'Employee record not found',
                    'records': []
                }, status=status.HTTP_200_OK)

            employees = Employee.objects.filter(
                company=current_employee.company,
                deleted_at__isnull=True
            ).select_related('user').order_by('user__name')

            if request.user.role not in ['HR', 'ADMIN']:
                employees = employees.filter(id=current_employee.id)

            records = [
                {'id': str(emp.id), 'name': emp.user.name}
                for emp in employees
            ]

            return Response({
                'status': True,
                'records': records
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error loading employee options',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class LoanAdvanceStats(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            current_employee = Employee.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()

            if not current_employee:
                return Response({
                    'status': False,
                    'message': 'Employee record not found',
                    'records': {}
                }, status=status.HTTP_200_OK)

            query = Q(employee__company=current_employee.company, deleted_at__isnull=True, status='Active')
            if request.user.role not in ['HR', 'ADMIN']:
                query &= Q(employee=current_employee)

            stats = LoanAdvance.objects.filter(query).aggregate(
                active_loans=Count('id'),
                total_principal=Sum('principal_amount'),
                total_outstanding=Sum('outstanding_balance'),
                total_emi=Sum('emi_amount')
            )

            active_loans = stats.get('active_loans') or 0
            total_emi = stats.get('total_emi') or Decimal('0')
            average_emi = (total_emi / active_loans) if active_loans else Decimal('0')

            return Response({
                'status': True,
                'records': {
                    'active_loans': active_loans,
                    'total_principal': stats.get('total_principal') or Decimal('0'),
                    'total_outstanding': stats.get('total_outstanding') or Decimal('0'),
                    'average_emi': average_emi
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching loan statistics',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class LoanAdvanceSchedule(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            current_employee = Employee.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()

            if not current_employee:
                return Response({
                    'status': False,
                    'message': 'Employee record not found',
                    'records': {}
                }, status=status.HTTP_200_OK)

            query = Q(employee__company=current_employee.company, deleted_at__isnull=True, status='Active')
            if request.user.role not in ['HR', 'ADMIN']:
                query &= Q(employee=current_employee)

            loans = LoanAdvance.objects.filter(query)
            today = timezone.now().date()
            window_end = today + timedelta(days=30)

            due_soon = 0
            at_risk = 0
            for loan in loans:
                if loan.next_deduction_date and today <= loan.next_deduction_date <= window_end:
                    due_soon += 1
                principal = float(loan.principal_amount or 0)
                balance = float(loan.outstanding_balance or 0)
                if principal > 0 and balance / principal > 0.5:
                    at_risk += 1

            return Response({
                'status': True,
                'records': {
                    'active_accounts': loans.count(),
                    'due_in_30_days': due_soon,
                    'at_risk_accounts': at_risk,
                    'message': f'Repayment schedule ready: {due_soon} due soon, {at_risk} high-balance accounts.'
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error generating repayment schedule',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

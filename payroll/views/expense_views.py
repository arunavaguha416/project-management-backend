# payroll/views/expense_views.py

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
from payroll.serializers.expense_serializer import (
    ExpenseCategorySerializer, ExpenseClaimSerializer,
    ExpenseApprovalWorkflowSerializer, ExpenseStatsSerializer
)
from hr_management.models.hr_management_models import Employee
from authentication.models.user import User


class ExpenseCategoryList(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            search_data = request.data
            page = int(search_data.get('page', 1))
            page_size = int(search_data.get('page_size', 10))
            search_name = search_data.get('name', '')

            query = Q()
            if search_name:
                query &= Q(name__icontains=search_name)

            categories = ExpenseCategory.objects.filter(query).order_by('name')

            if categories.exists():
                if page:
                    paginator = Paginator(categories, page_size)
                    try:
                        paginated_categories = paginator.page(page)
                    except:
                        paginated_categories = paginator.page(1)

                    serializer = ExpenseCategorySerializer(paginated_categories, many=True)
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'current_page': page,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = ExpenseCategorySerializer(categories, many=True)
                    return Response({
                        'status': True,
                        'count': categories.count(),
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'No expense categories found',
                    'count': 0,
                    'records': []
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching expense categories',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ExpenseCategoryAdd(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            serializer = ExpenseCategorySerializer(data=request.data)
            if serializer.is_valid():
                category = serializer.save()
                return Response({
                    'status': True,
                    'message': 'Expense category added successfully',
                    'records': ExpenseCategorySerializer(category).data
                }, status=status.HTTP_200_OK)

            return Response({
                'status': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error adding expense category',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ExpenseCategoryUpdate(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            category_id = request.data.get('id')
            category = ExpenseCategory.objects.filter(id=category_id).first()

            if not category:
                return Response({
                    'status': False,
                    'message': 'Expense category not found'
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = ExpenseCategorySerializer(category, data=request.data, partial=True)
            if serializer.is_valid():
                updated_category = serializer.save()
                return Response({
                    'status': True,
                    'message': 'Expense category updated successfully',
                    'records': ExpenseCategorySerializer(updated_category).data
                }, status=status.HTTP_200_OK)

            return Response({
                'status': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error updating expense category',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ExpenseCategoryDelete(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            category_id = request.data.get('category_id')
            if not category_id:
                return Response({
                    'status': False,
                    'message': 'Category ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            category = ExpenseCategory.objects.filter(id=category_id).first()
            if not category:
                return Response({
                    'status': False,
                    'message': 'Expense category not found'
                }, status=status.HTTP_404_NOT_FOUND)

            category.soft_delete()
            return Response({
                'status': True,
                'message': 'Expense category deleted successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error deleting expense category',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ExpenseClaimList(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            search_data = request.data
            page = int(search_data.get('page', 1))
            page_size = int(search_data.get('page_size', 10))
            status_filter = search_data.get('status', '')
            employee_id = search_data.get('employee_id')
            category_id = search_data.get('category_id')
            date_from = search_data.get('date_from')
            date_to = search_data.get('date_to')

            # Base query - users can see their own claims
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
            if status_filter:
                query &= Q(status=status_filter)
            if employee_id and request.user.role in ['HR', 'ADMIN']:
                query &= Q(employee_id=employee_id)
            if category_id:
                query &= Q(category_id=category_id)
            if date_from:
                query &= Q(expense_date__gte=date_from)
            if date_to:
                query &= Q(expense_date__lte=date_to)

            claims = ExpenseClaim.objects.filter(query).select_related(
                'employee__user', 'category', 'reviewed_by'
            ).order_by('-created_at')

            if claims.exists():
                paginator = Paginator(claims, page_size)
                try:
                    paginated_claims = paginator.page(page)
                except:
                    paginated_claims = paginator.page(1)

                serializer = ExpenseClaimSerializer(paginated_claims, many=True, context={'request': request})
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
                    'message': 'No expense claims found',
                    'count': 0,
                    'records': []
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching expense claims',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ExpenseClaimAdd(APIView):
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

            # Add employee to data
            data = request.data.copy()
            data['employee'] = employee.id

            serializer = ExpenseClaimSerializer(data=data)
            if serializer.is_valid():
                claim = serializer.save()

                # Process receipt if uploaded
                if 'receipt_image' in data and data['receipt_image']:
                    self.process_receipt(claim, data['receipt_image'])

                return Response({
                    'status': True,
                    'message': 'Expense claim submitted successfully',
                    'records': ExpenseClaimSerializer(claim, context={'request': request}).data
                }, status=status.HTTP_200_OK)

            return Response({
                'status': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error submitting expense claim',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def process_receipt(self, claim, receipt_data):
        """Process receipt using OCR to extract text"""
        try:
            # Save receipt image and extract text using OCR
            # This is a simplified implementation
            if hasattr(claim, 'receipt_image') and claim.receipt_image:
                image = Image.open(claim.receipt_image.path)
                extracted_text = pytesseract.image_to_string(image)
                claim.receipt_text = extracted_text
                claim.save()
        except Exception as e:
            # Log error but don't fail the claim submission
            print(f"OCR processing failed: {str(e)}")


class ExpenseClaimUpdate(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            claim_id = request.data.get('id')
            claim = ExpenseClaim.objects.filter(id=claim_id).first()

            if not claim:
                return Response({
                    'status': False,
                    'message': 'Expense claim not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Check permissions
            if request.user.role not in ['HR', 'ADMIN'] and claim.employee.user != request.user:
                return Response({
                    'status': False,
                    'message': 'Insufficient permissions'
                }, status=status.HTTP_403_FORBIDDEN)

            # Only allow updates for Draft claims
            if claim.status not in ['Draft']:
                return Response({
                    'status': False,
                    'message': 'Cannot update submitted claims'
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer = ExpenseClaimSerializer(claim, data=request.data, partial=True)
            if serializer.is_valid():
                updated_claim = serializer.save()
                return Response({
                    'status': True,
                    'message': 'Expense claim updated successfully',
                    'records': ExpenseClaimSerializer(updated_claim, context={'request': request}).data
                }, status=status.HTTP_200_OK)

            return Response({
                'status': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error updating expense claim',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ExpenseClaimSubmit(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            claim_id = request.data.get('claim_id')
            claim = ExpenseClaim.objects.filter(id=claim_id).first()

            if not claim:
                return Response({
                    'status': False,
                    'message': 'Expense claim not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Check permissions
            if claim.employee.user != request.user:
                return Response({
                    'status': False,
                    'message': 'Insufficient permissions'
                }, status=status.HTTP_403_FORBIDDEN)

            if claim.status != 'Draft':
                return Response({
                    'status': False,
                    'message': 'Claim already submitted'
                }, status=status.HTTP_400_BAD_REQUEST)

            claim.status = 'Submitted'
            claim.submitted_at = timezone.now()
            claim.save()

            return Response({
                'status': True,
                'message': 'Expense claim submitted successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error submitting expense claim',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ExpenseClaimApprove(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Only HR and ADMIN can approve claims
            if request.user.role not in ['HR', 'ADMIN']:
                return Response({
                    'status': False,
                    'message': 'Insufficient permissions'
                }, status=status.HTTP_403_FORBIDDEN)

            claim_ids = request.data.get('claim_ids', [])
            action = request.data.get('action', 'approve')  # approve/reject
            comments = request.data.get('comments', '')
            reimbursement_amount = request.data.get('reimbursement_amount')

            if not claim_ids:
                return Response({
                    'status': False,
                    'message': 'No claim IDs provided'
                }, status=status.HTTP_400_BAD_REQUEST)

            claims = ExpenseClaim.objects.filter(id__in=claim_ids)
            updated_count = 0

            for claim in claims:
                if action == 'approve':
                    claim.status = 'Approved'
                    claim.reimbursement_amount = reimbursement_amount or claim.amount
                elif action == 'reject':
                    claim.status = 'Rejected'

                claim.reviewed_by = request.user
                claim.reviewed_at = timezone.now()
                claim.approval_comments = comments
                claim.save()
                updated_count += 1

            return Response({
                'status': True,
                'message': f'{updated_count} expense claims {action}d successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': f'Error {action}ing expense claims',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ExpenseClaimDelete(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            claim_id = request.data.get('claim_id')
            if not claim_id:
                return Response({
                    'status': False,
                    'message': 'Claim ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            claim = ExpenseClaim.objects.filter(id=claim_id).first()
            if not claim:
                return Response({
                    'status': False,
                    'message': 'Expense claim not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Check permissions
            if request.user.role not in ['HR', 'ADMIN'] and claim.employee.user != request.user:
                return Response({
                    'status': False,
                    'message': 'Insufficient permissions'
                }, status=status.HTTP_403_FORBIDDEN)

            # Only allow deletion of Draft claims
            if claim.status not in ['Draft']:
                return Response({
                    'status': False,
                    'message': 'Cannot delete submitted claims'
                }, status=status.HTTP_400_BAD_REQUEST)

            claim.soft_delete()
            return Response({
                'status': True,
                'message': 'Expense claim deleted successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error deleting expense claim',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ExpenseStats(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Filter by date range if provided
            date_from = request.data.get('date_from')
            date_to = request.data.get('date_to')

            if not date_from:
                date_from = date.today().replace(day=1)  # First day of current month
            if not date_to:
                date_to = date.today()

            # Base query
            if request.user.role in ['HR', 'ADMIN']:
                query = Q()
            else:
                employee = Employee.objects.filter(user=request.user).first()
                if not employee:
                    return Response({
                        'status': False,
                        'message': 'Employee record not found',
                        'records': {}
                    }, status=status.HTTP_200_OK)
                query = Q(employee=employee)

            # Apply date filter
            query &= Q(expense_date__range=[date_from, date_to])
            claims = ExpenseClaim.objects.filter(query)

            # Calculate statistics
            stats = claims.aggregate(
                total_claims=Count('id'),
                total_amount_claimed=Sum('amount'),
                total_amount_approved=Sum('reimbursement_amount'),
                pending_approvals=Count('id', filter=Q(status__in=['Submitted', 'Under Review']))
            )

            # Calculate average processing days
            approved_claims = claims.filter(
                status__in=['Approved', 'Paid'],
                submitted_at__isnull=False,
                reviewed_at__isnull=False
            )

            if approved_claims.exists():
                processing_times = []
                for claim in approved_claims:
                    processing_time = (claim.reviewed_at - claim.submitted_at).days
                    processing_times.append(processing_time)
                stats['average_processing_days'] = sum(processing_times) / len(processing_times)
            else:
                stats['average_processing_days'] = 0

            # Handle None values
            for key, value in stats.items():
                if value is None:
                    stats[key] = 0

            # Calculate paid amount
            stats['total_amount_paid'] = claims.filter(status='Paid').aggregate(
                total=Sum('reimbursement_amount')
            )['total'] or 0

            serializer = ExpenseStatsSerializer(stats)
            return Response({
                'status': True,
                'records': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching expense statistics',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ReceiptUpload(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            claim_id = request.data.get('claim_id')
            receipt_file = request.FILES.get('receipt_image')

            if not claim_id or not receipt_file:
                return Response({
                    'status': False,
                    'message': 'Claim ID and receipt file are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            claim = ExpenseClaim.objects.filter(id=claim_id).first()
            if not claim:
                return Response({
                    'status': False,
                    'message': 'Expense claim not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Check permissions
            if claim.employee.user != request.user:
                return Response({
                    'status': False,
                    'message': 'Insufficient permissions'
                }, status=status.HTTP_403_FORBIDDEN)

            # Save receipt
            claim.receipt_image = receipt_file
            claim.save()

            # Process OCR
            self.process_receipt_ocr(claim)

            return Response({
                'status': True,
                'message': 'Receipt uploaded successfully',
                'records': {
                    'receipt_url': claim.receipt_image.url if claim.receipt_image else None,
                    'extracted_text': claim.receipt_text
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error uploading receipt',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def process_receipt_ocr(self, claim):
        """Extract text from receipt using OCR"""
        try:
            if claim.receipt_image:
                image = Image.open(claim.receipt_image.path)
                extracted_text = pytesseract.image_to_string(image)

                # Simple extraction of merchant name and amount
                lines = extracted_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not claim.merchant_name:
                        claim.merchant_name = line[:200]  # First non-empty line as merchant
                        break

                claim.receipt_text = extracted_text
                claim.save()
        except Exception as e:
            print(f"OCR processing failed: {str(e)}")


class ReceiptProcess(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            claim_id = request.data.get('claim_id')
            claim = ExpenseClaim.objects.filter(id=claim_id).first()

            if not claim:
                return Response({
                    'status': False,
                    'message': 'Expense claim not found'
                }, status=status.HTTP_404_NOT_FOUND)

            if not claim.receipt_image:
                return Response({
                    'status': False,
                    'message': 'No receipt image found'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Reprocess OCR
            self.process_receipt_ocr(claim)

            return Response({
                'status': True,
                'message': 'Receipt processed successfully',
                'records': {
                    'extracted_text': claim.receipt_text,
                    'merchant_name': claim.merchant_name
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error processing receipt',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def process_receipt_ocr(self, claim):
        """Extract text from receipt using OCR - same as in ReceiptUpload"""
        try:
            if claim.receipt_image:
                image = Image.open(claim.receipt_image.path)
                extracted_text = pytesseract.image_to_string(image)

                lines = extracted_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not claim.merchant_name:
                        claim.merchant_name = line[:200]
                        break

                claim.receipt_text = extracted_text
                claim.save()
        except Exception as e:
            print(f"OCR processing failed: {str(e)}")


class ExpenseExport(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Export expense data to CSV
            date_from = request.data.get('date_from')
            date_to = request.data.get('date_to')
            export_format = request.data.get('format', 'csv')

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

            # Apply date filter
            if date_from and date_to:
                query &= Q(expense_date__range=[date_from, date_to])

            claims = ExpenseClaim.objects.filter(query).select_related(
                'employee__user', 'category'
            ).order_by('-expense_date')

            # Generate export data
            export_data = []
            for claim in claims:
                export_data.append({
                    'employee_name': claim.employee.user.name,
                    'employee_email': claim.employee.user.email,
                    'category': claim.category.name,
                    'title': claim.title,
                    'amount': str(claim.amount),
                    'expense_date': claim.expense_date.strftime('%Y-%m-%d'),
                    'status': claim.status,
                    'reimbursement_amount': str(claim.reimbursement_amount or 0),
                    'submitted_at': claim.submitted_at.strftime('%Y-%m-%d %H:%M') if claim.submitted_at else '',
                    'approved_at': claim.reviewed_at.strftime('%Y-%m-%d %H:%M') if claim.reviewed_at else ''
                })

            return Response({
                'status': True,
                'message': f'Exported {len(export_data)} expense records',
                'records': export_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error exporting expense data',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

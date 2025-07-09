# company/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.db.models import Q
from django.core.paginator import Paginator
from company.models.company_model import Company
from company.serializers.serializers import CompanySerializer

class CompanyAdd(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request):
        try:
            serializer = CompanySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': True,
                    'message': 'Company added successfully',
                    'records': serializer.data
                }, status=status.HTTP_200_OK)
            return Response({
                'status': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CompanyList(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            companies = Company.objects.filter().order_by('-created_at')
            if companies.exists():
                serializer = CompanySerializer(companies, many=True)
                return Response({
                    'status': True,
                    'count': companies.count(),
                    'records': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Companies not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CompanyDetails(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            company_id = request.data.get('id')
            if company_id:
                company = Company.objects.filter(id=company_id).values('id', 'name', 'description').first()
                if company:
                    return Response({'status': True, 'records': company}, status=status.HTTP_200_OK)
                else:
                    return Response({'status': False, 'message': 'Company not found'}, status=status.HTTP_200_OK)
            else:
                return Response({'status': False, 'message': 'Please provide companyId'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CompanyUpdate(APIView):
    permission_classes = (IsAdminUser,)

    def put(self, request):
        try:
            company_id = request.data.get('id')
            company = Company.objects.filter(id=company_id).first()
            if company:
                if not company.deleted_at:
                    serializer = CompanySerializer(company, data=request.data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return Response({'status': True, 'message': 'Company updated successfully'}, status=status.HTTP_200_OK)
                    return Response({'status': False, 'message': 'Invalid data', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'status': False, 'message': 'Cannot update a deleted company'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'status': False, 'message': 'Company not found'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CompanyDelete(APIView):
    permission_classes = (IsAdminUser,)

    def delete(self, request, company_id):
        try:
            company = Company.objects.filter(id=company_id).first()
            if company:
                if not company.deleted_at:
                    company.soft_delete()
                    return Response({'status': True, 'message': 'Company deleted successfully'}, status=status.HTTP_200_OK)
                else:
                    return Response({'status': False, 'message': 'Company is already deleted'}, status=status.HTTP_200_OK)
            return Response({'status': False, 'message': 'Company not found'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RestoreCompany(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request):
        try:
            company_id = request.data.get('id')
            company = Company.all_objects.filter(id=company_id).first()
            if company:
                if company.deleted_at:
                    company.deleted_at = None
                    company.save()
                    return Response({'status': True, 'message': 'Company restored successfully'}, status=status.HTTP_200_OK)
                else:
                    return Response({'status': False, 'message': 'Company is not deleted'}, status=status.HTTP_200_OK)
            return Response({'status': False, 'message': 'Company not found'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

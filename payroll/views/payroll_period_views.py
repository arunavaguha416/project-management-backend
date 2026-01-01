from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from payroll.models.payroll_models import *
from payroll.serializers.payroll_serializer import *
from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework.response import Response
from rest_framework import status

class PayrollPeriodList(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            periods = PayrollPeriod.objects.all().order_by('-start_date')
            serializer = PayrollPeriodSerializer(periods, many=True)

            return Response({
                'status': True,
                'records': serializer.data
            })

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Failed to load payroll periods',
                'error': str(e)
            }, status=500)


class PayrollPeriodPaginatedList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            data = request.data

            page = int(data.get("page", 1))
            page_size = int(data.get("page_size", 10))
            search = data.get("search", "")

            query = Q()
            if search:
                query &= (
                    Q(name__icontains=search) |
                    Q(financial_year__icontains=search)
                )

            periods = PayrollPeriod.objects.filter(query).order_by("-start_date")

            paginator = Paginator(periods, page_size)

            try:
                paginated_periods = paginator.page(page)
            except Exception:
                paginated_periods = paginator.page(1)

            serializer = PayrollPeriodSerializer(paginated_periods, many=True)

            return Response({
                "status": True,
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "records": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": False,
                "message": "Failed to load payroll periods",
                "error": str(e),
                "count": 0,
                "records": []
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
                }, status=200)

            return Response({
                'status': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=400)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error creating payroll period',
                'error': str(e)
            }, status=500)
        


class PayrollPeriodUpdateView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        period_id = request.data.get("id")
        if not period_id:
            return Response(
                {"status": False, "message": "id is required"},
                status=400
            )

        period = PayrollPeriod.objects.filter(id=period_id).first()
        if not period:
            return Response(
                {"status": False, "message": "Payroll period not found"},
                status=404
            )

        serializer = PayrollPeriodSerializer(period, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "Payroll period updated",
                "record": serializer.data
            })

        return Response({
            "status": False,
            "errors": serializer.errors
        }, status=400)

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.db.models import Q
from time_tracking.models.time_tracking_models import TimeEntry
from time_tracking.serializers.time_tracking_serializer import TimeEntrySerializer
from django.core.paginator import Paginator
import datetime
from uuid import UUID

class TimeEntryAdd(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer = TimeEntrySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response({
                    'status': True,
                    'message': 'Time entry added successfully',
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
                'message': 'An error occurred while adding the time entry',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class TimeEntryList(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)
            search_description = search_data.get('description', '')

            query = Q(user=request.user) | Q(task__project__owner=request.user)
            if search_description:
                query &= Q(description__icontains=search_description)

            time_entries = TimeEntry.objects.filter(query).order_by('-created_at')

            if time_entries.exists():
                if page is not None:
                    paginator = Paginator(time_entries, page_size)
                    paginated_entries = paginator.get_page(page)
                    serializer = TimeEntrySerializer(paginated_entries, many=True)
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = TimeEntrySerializer(time_entries, many=True)
                    return Response({
                        'status': True,
                        'count': time_entries.count(),
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Time entries not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class PublishedTimeEntryList(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            time_entries = TimeEntry.objects.filter(published_at__isnull=False).values('id', 'description').order_by('-created_at')
            if time_entries.exists():
                return Response({
                    'status': True,
                    'records': time_entries
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Time entries not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class DeletedTimeEntryList(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)
            search_description = search_data.get('description', '')

            query = Q(deleted_at__isnull=False)
            if search_description:
                query &= Q(description__icontains=search_description)

            time_entries = TimeEntry.all_objects.filter(query).order_by('-created_at')

            if time_entries.exists():
                if page is not None:
                    paginator = Paginator(time_entries, page_size)
                    paginated_entries = paginator.get_page(page)
                    serializer = TimeEntrySerializer(paginated_entries, many=True)
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = TimeEntrySerializer(time_entries, many=True)
                    return Response({
                        'status': True,
                        'count': time_entries.count(),
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Deleted time entries not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class TimeEntryDetails(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            time_entry_id = request.data.get('id')
            if time_entry_id:
                time_entry = TimeEntry.objects.filter(
                    Q(id=time_entry_id, user=request.user) |
                    Q(id=time_entry_id, task__project__owner=request.user)
                ).values('id', 'duration', 'date', 'description').first()
                if time_entry:
                    return Response({
                        'status': True,
                        'records': time_entry
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': False,
                        'message': 'Time entry not found',
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Please provide timeEntryId'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching time entry details',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class TimeEntryUpdate(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request):
        try:
            time_entry_id = request.data.get('id')
            time_entry = TimeEntry.objects.filter(id=time_entry_id).first()
            if time_entry:
                serializer = TimeEntrySerializer(time_entry, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'status': True,
                        'message': 'Time entry updated successfully'
                    }, status=status.HTTP_200_OK)
                return Response({
                    'status': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'status': False,
                'message': 'Time entry not found'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while updating the time entry',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class ChangeTimeEntryPublishStatus(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request):
        try:
            time_entry_id = request.data.get('id')
            publish = request.data.get('status')
            if publish == '1':
                data = {'published_at': datetime.datetime.now()}
            elif publish == '0':
                data = {'published_at': None}
            time_entry = TimeEntry.objects.get(id=time_entry_id)
            serializer = TimeEntrySerializer(time_entry, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': True,
                    'message': 'Publish status updated successfully',
                }, status=status.HTTP_200_OK)
            return Response({
                'status': False,
                'message': 'Unable to update publish status',
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)

class TimeEntryDelete(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request, time_entry_id: UUID):
        try:
            time_entry = TimeEntry.objects.filter(id=time_entry_id).first()
            if time_entry:
                # time_entry.soft_delete():
                return Response({
                    'status': True,
                    'message': 'Time entry deleted successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Time entry not found'
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class RestoreTimeEntry(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            time_entry_id = request.data.get('id')
            time_entry = TimeEntry.all_objects.get(id=time_entry_id)
            if time_entry:
                time_entry.delete_at = None
                time_entry.save()
                return Response({
                    'status': True,
                    'message': 'Time entry restored successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Time entry not found'
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
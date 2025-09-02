from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q, Sum
from time_tracking.models.time_tracking_models import TimeEntry
from time_tracking.serializers.time_tracking_serializer import TimeEntrySerializer, UserTimeStatsSerializer
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, date, timedelta
from uuid import UUID

class RecordLoginTime(APIView):
    """Record user login time - called when user logs in"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            today = date.today()
            login_time = timezone.now()
            
            # Get or create time entry for today
            time_entry, created = TimeEntry.objects.get_or_create(
                user=user,
                date=today,
                defaults={
                    'login_time': login_time,
                    'description': f'Login tracked automatically'
                }
            )
            
            if not created:
                # Update login time if entry exists but no login time recorded
                if not time_entry.login_time:
                    time_entry.login_time = login_time
                    time_entry.save()
            
            serializer = TimeEntrySerializer(time_entry)
            
            return Response({
                'status': True,
                'message': 'Login time recorded successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error recording login time',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class RecordLogoutTime(APIView):
    """Record user logout time - called when user logs out"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            today = date.today()
            logout_time = timezone.now()
            
            # Find today's time entry
            time_entry = TimeEntry.objects.filter(
                user=user,
                date=today
            ).first()
            
            if time_entry:
                time_entry.logout_time = logout_time
                time_entry.save()  # This will auto-calculate duration
                
                serializer = TimeEntrySerializer(time_entry)
                
                return Response({
                    'status': True,
                    'message': 'Logout time recorded successfully',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'No login record found for today'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error recording logout time',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class TimeEntryList(APIView):
    """List time entries with filtering and pagination"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            search_data = request.data
            page = int(search_data.get('page', 1))
            page_size = int(search_data.get('page_size', 10))
            date_from = search_data.get('date_from')
            date_to = search_data.get('date_to')
            user_id = search_data.get('user_id')
            
            # Base query - users can see their own entries
            query = Q(user=request.user)
            
            # HR and MANAGER can see other users' entries
            if request.user.role in ['HR', 'MANAGER']:
                if user_id:
                    query = Q(user_id=user_id)
                else:
                    query = Q()  # See all entries
            
            # Apply date filters
            if date_from:
                query &= Q(date__gte=date_from)
            if date_to:
                query &= Q(date__lte=date_to)
            
            time_entries = TimeEntry.objects.filter(query).order_by('-date', '-created_at')
            
            if time_entries.exists():
                paginator = Paginator(time_entries, page_size)
                try:
                    paginated_entries = paginator.page(page)
                except Exception:
                    paginated_entries = paginator.page(1)
                
                serializer = TimeEntrySerializer(paginated_entries, many=True)
                
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
                    'message': 'No time entries found',
                    'count': 0,
                    'records': []
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching time entries',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class UserTimeStats(APIView):
    """Get user time tracking statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            today = date.today()
            
            # Get all time entries for the user
            time_entries = TimeEntry.objects.filter(user=user)
            
            # Calculate total days worked
            total_days = time_entries.filter(duration__isnull=False).count()
            
            # Calculate total hours worked
            total_duration = time_entries.aggregate(
                total=Sum('duration')
            )['total']
            
            total_hours = "0h 0m"
            if total_duration:
                total_seconds = total_duration.total_seconds()
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                total_hours = f"{hours}h {minutes}m"
            
            # Calculate average hours per day
            avg_hours = "0h 0m"
            if total_days > 0 and total_duration:
                avg_seconds = total_duration.total_seconds() / total_days
                hours = int(avg_seconds // 3600)
                minutes = int((avg_seconds % 3600) // 60)
                avg_hours = f"{hours}h {minutes}m"
            
            # Current week hours
            week_start = today - timedelta(days=today.weekday())
            week_entries = time_entries.filter(date__gte=week_start, date__lte=today)
            week_duration = week_entries.aggregate(total=Sum('duration'))['total']
            
            current_week_hours = "0h 0m"
            if week_duration:
                total_seconds = week_duration.total_seconds()
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                current_week_hours = f"{hours}h {minutes}m"
            
            # Current month hours
            month_start = today.replace(day=1)
            month_entries = time_entries.filter(date__gte=month_start, date__lte=today)
            month_duration = month_entries.aggregate(total=Sum('duration'))['total']
            
            current_month_hours = "0h 0m"
            if month_duration:
                total_seconds = month_duration.total_seconds()
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                current_month_hours = f"{hours}h {minutes}m"
            
            # Today's entry
            today_entry = time_entries.filter(date=today).first()
            today_status = "Not logged in"
            if today_entry:
                if today_entry.login_time and not today_entry.logout_time:
                    today_status = "Currently logged in"
                elif today_entry.login_time and today_entry.logout_time:
                    today_status = "Completed"
                else:
                    today_status = "No login recorded"
            
            stats_data = {
                'total_days': total_days,
                'total_hours': total_hours,
                'average_hours_per_day': avg_hours,
                'current_week_hours': current_week_hours,
                'current_month_hours': current_month_hours,
                'today_status': today_status,
                'today_entry': TimeEntrySerializer(today_entry).data if today_entry else None
            }
            
            return Response({
                'status': True,
                'data': stats_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching time statistics',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class ManualTimeEntry(APIView):
    """Add manual time entry (for admins/HR)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Only HR and ADMIN can add manual entries
            if request.user.role not in ['HR', 'ADMIN']:
                return Response({
                    'status': False,
                    'message': 'Insufficient permissions'
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = TimeEntrySerializer(data=request.data)
            if serializer.is_valid():
                time_entry = serializer.save()
                return Response({
                    'status': True,
                    'message': 'Manual time entry added successfully',
                    'data': TimeEntrySerializer(time_entry).data
                }, status=status.HTTP_200_OK)
            
            return Response({
                'status': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error adding manual time entry',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class TimeEntryUpdate(APIView):
    """Update time entry"""
    permission_classes = [IsAuthenticated]
    
    def put(self, request):
        try:
            entry_id = request.data.get('id')
            
            # Find the time entry
            time_entry = TimeEntry.objects.filter(id=entry_id).first()
            
            if not time_entry:
                return Response({
                    'status': False,
                    'message': 'Time entry not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check permissions
            if request.user.role not in ['HR', 'ADMIN'] and time_entry.user != request.user:
                return Response({
                    'status': False,
                    'message': 'Insufficient permissions'
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = TimeEntrySerializer(time_entry, data=request.data, partial=True)
            if serializer.is_valid():
                updated_entry = serializer.save()
                return Response({
                    'status': True,
                    'message': 'Time entry updated successfully',
                    'data': TimeEntrySerializer(updated_entry).data
                }, status=status.HTTP_200_OK)
            
            return Response({
                'status': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error updating time entry',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class TimeEntryDelete(APIView):
    """Delete time entry"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, entry_id):
        try:
            # Find the time entry
            time_entry = TimeEntry.objects.filter(id=entry_id).first()
            
            if not time_entry:
                return Response({
                    'status': False,
                    'message': 'Time entry not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check permissions
            if request.user.role not in ['HR', 'ADMIN']:
                return Response({
                    'status': False,
                    'message': 'Insufficient permissions'
                }, status=status.HTTP_403_FORBIDDEN)
            
            time_entry.soft_delete()
            
            return Response({
                'status': True,
                'message': 'Time entry deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error deleting time entry',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q, Sum
from time_tracking.models.time_tracking_models import TimeEntry
from time_tracking.serializers.time_tracking_serializer import TimeEntrySerializer, UserTimeStatsSerializer
from authentication.models.user import User
from hr_management.models.hr_management_models import Employee
from projects.models.project_member_model import ProjectMember
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, date, timedelta
from uuid import UUID

def _can_view_all_entries(user):
    return user.role in ['HR', 'MANAGER', 'ADMIN']


def _get_allowed_user_ids_for_time_tracking(user):
    current_employee = Employee.objects.filter(user=user, deleted_at__isnull=True).first()
    if not current_employee or not current_employee.company:
        return User.objects.filter(id=user.id, deleted_at__isnull=True).values_list('id', flat=True)

    if user.role in ['HR', 'ADMIN']:
        return User.objects.filter(
            employee__company=current_employee.company,
            employee__deleted_at__isnull=True,
            deleted_at__isnull=True
        ).distinct().values_list('id', flat=True)

    if user.role == 'MANAGER':
        team_user_ids = ProjectMember.objects.filter(
            project__manager=current_employee,
            project__deleted_at__isnull=True,
            is_active=True
        ).values_list('user_id', flat=True)
        return User.objects.filter(
            Q(id__in=team_user_ids) | Q(id=user.id),
            deleted_at__isnull=True
        ).distinct().values_list('id', flat=True)

    return User.objects.filter(id=user.id, deleted_at__isnull=True).values_list('id', flat=True)

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
            search = (search_data.get('search') or '').strip()
            
            allowed_user_ids = [str(u) for u in _get_allowed_user_ids_for_time_tracking(request.user)]
            query = Q(user_id__in=allowed_user_ids)
            if user_id:
                if str(user_id) not in allowed_user_ids:
                    return Response({
                        'status': False,
                        'message': 'Insufficient permissions'
                    }, status=status.HTTP_403_FORBIDDEN)
                query &= Q(user_id=user_id)
            
            # Apply date filters
            if date_from:
                query &= Q(date__gte=date_from)
            if date_to:
                query &= Q(date__lte=date_to)

            if search:
                query &= (
                    Q(description__icontains=search)
                    | Q(user__name__icontains=search)
                    | Q(user__email__icontains=search)
                    | Q(user__username__icontains=search)
                    | Q(date__icontains=search)
                )
            
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
    
    def _build_stats(self, user):
        try:
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
            
            return {
                'status': True,
                'data': stats_data
            }, status.HTTP_200_OK
            
        except Exception as e:
            return {
                'status': False,
                'message': 'Error fetching time statistics',
                'error': str(e)
            }, status.HTTP_400_BAD_REQUEST

    def get(self, request):
        payload, code = self._build_stats(request.user)
        return Response(payload, status=code)

    def post(self, request):
        user = request.user
        user_id = request.data.get('user_id')

        if user_id:
            allowed_user_ids = [str(u) for u in _get_allowed_user_ids_for_time_tracking(user)]
            if str(user_id) not in allowed_user_ids:
                return Response({
                    'status': False,
                    'message': 'Insufficient permissions'
                }, status=status.HTTP_403_FORBIDDEN)
            target = User.objects.filter(id=user_id, deleted_at__isnull=True).first()
            if target:
                user = target

        payload, code = self._build_stats(user)
        return Response(payload, status=code)

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

            target_user = request.user
            user_id = request.data.get('user_id')
            if user_id:
                target = User.objects.filter(id=user_id, deleted_at__isnull=True).first()
                if not target:
                    return Response({
                        'status': False,
                        'message': 'Selected user not found'
                    }, status=status.HTTP_400_BAD_REQUEST)
                target_user = target

            serializer = TimeEntrySerializer(data=request.data)
            if serializer.is_valid():
                login_time = serializer.validated_data.get('login_time')
                logout_time = serializer.validated_data.get('logout_time')
                if login_time and logout_time and logout_time < login_time:
                    return Response({
                        'status': False,
                        'message': 'logout_time cannot be earlier than login_time'
                    }, status=status.HTTP_400_BAD_REQUEST)

                time_entry = serializer.save(user=target_user)
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
                login_time = serializer.validated_data.get('login_time', time_entry.login_time)
                logout_time = serializer.validated_data.get('logout_time', time_entry.logout_time)
                if login_time and logout_time and logout_time < login_time:
                    return Response({
                        'status': False,
                        'message': 'logout_time cannot be earlier than login_time'
                    }, status=status.HTTP_400_BAD_REQUEST)

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


class TimeTrackingUserList(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            search = (request.data.get('search') or '').strip()
            page = int(request.data.get('page', 1))
            page_size = int(request.data.get('page_size', 20))

            allowed_user_ids = list(_get_allowed_user_ids_for_time_tracking(request.user))
            query = Q(id__in=allowed_user_ids, deleted_at__isnull=True, is_active=True)
            if search:
                query &= (
                    Q(name__icontains=search) |
                    Q(email__icontains=search) |
                    Q(username__icontains=search)
                )

            users = User.objects.filter(query).order_by('name')
            if not users.exists():
                return Response({
                    'status': True,
                    'count': 0,
                    'num_pages': 0,
                    'current_page': 1,
                    'records': []
                }, status=status.HTTP_200_OK)

            paginator = Paginator(users, page_size)
            paged = paginator.page(page if page <= paginator.num_pages else 1)

            records = [{
                'id': str(u.id),
                'name': u.name,
                'email': u.email,
                'username': u.username,
                'role': u.role
            } for u in paged]

            return Response({
                'status': True,
                'count': paginator.count,
                'num_pages': paginator.num_pages,
                'current_page': page,
                'records': records
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching users',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

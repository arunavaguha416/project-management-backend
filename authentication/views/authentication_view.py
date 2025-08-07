from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from hr_management.serializers.hr_management_serializer import EmployeeSerializer
from ..serializers.serializer import *
from django.contrib.auth import authenticate
from django.contrib.auth.signals import user_logged_in
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from projects.models.project_model import Project
from projects.models.task_model import Task
from teams.models.team_model import Team
from hr_management.models.hr_management_models import Employee, LeaveRequest, Attendance

from django.db.models import Count, Q
from teams.models.team_members_mapping import TeamMembersMapping

class Login(APIView):
    """
    API View for user login. Accessible by any users.
    """
    permission_classes = (AllowAny,)

    def post(self, request):
        """
        Handle POST request for user login.
        Authenticates users and returns appropriate tokens based on user type (admin/non-admin).
        """
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            isAdmin = request.data.get('is_admin', False)
            
            # Authenticate user with provided credentials
            user = authenticate(username=username, password=password)
            
            if user is not None:
                # Generate token for authenticated user
                token = RefreshToken.for_user(user)
                # Prepare user data for response
                user_data = {
                    'email': user.email,
                    'name': user.name,
                    'role': user.role,
                    'is_admin': user.is_superuser
                }
                
                # Handle different login scenarios based on user type and requested login type
                if isAdmin is True and user.is_superuser is True:
                    return Response({
                        'status': True,
                        'message': 'Admin login successful',
                        'user': user_data,
                        'role': user.role,
                        'refresh': str(token),
                        'access': str(token.access_token),
                    }, status=status.HTTP_200_OK)
                    
                elif isAdmin is True and user.is_superuser is False:
                    return Response({
                        'status': False,
                        'message': 'The user is not admin'
                    }, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
                    
                elif isAdmin is False and user.is_superuser is False:
                    return Response({
                        'status': True,
                        'message': 'User login successful',
                        'user': user_data,
                        'is_admin': user.is_superuser,
                        'refresh': str(token),
                        'access': str(token.access_token),
                    }, status=status.HTTP_200_OK)
                    
                elif isAdmin is False and user.is_superuser is True:
                    return Response({
                        'status': False,
                        'message': 'Please redirect to Admin panel for Admin login'
                    }, status=status.HTTP_303_SEE_OTHER)
            else:
                # Authentication failed
                return Response({
                    'status': False,
                    'message': 'Invalid credentials',
                    'username': username,
                    'password':password,
                    'user':user,
                }, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
                
        except Exception as e:
            # Handle any unexpected errors
            return Response({
                'status': False,
                'message': 'An error occurred during login',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class Registration(APIView):
    """
    API View for user registration. Accessible by any users.
    """
    permission_classes = ()

    def post(self, request):
        try:
            data = request.data.copy()
            with transaction.atomic():
                # Serialize and validate User
                user_serializer = UserSerializer(data=data, partial=True)
                if not user_serializer.is_valid():
                    return Response({
                        'status': False,
                        'message': 'Invalid user data provided',
                        'errors': user_serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Save User (this also handles password hashing)
                user = user_serializer.save()

                # Create Employee DIRECTLY, so FK is always present
                employee = Employee.objects.create(
                    user=user,
                    salary=data.get('salary'),
                    date_of_joining=data.get('date_of_joining'),
                    designation=data.get('designation'),
                    company_id=data.get('comp_id'),
                    department_id=data.get('dept_id'),
                    # phone=data.get('phone', '')  # Uncomment if you want phone support
                )

                # Use serializer for Employee representation in response
                employee_data = EmployeeSerializer(employee).data

                return Response({
                    'status': True,
                    'message': 'User registered successfully',
                    'data': {
                        'user': user_serializer.data,
                        'employee': employee_data
                    }
                }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred during registration',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class Logout(APIView):
    """
    API View for user logout. Only accessible by authenticated users.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """
        Handle POST request for user logout. Blacklists the user's refresh token to prevent further use.
        """
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            
            # Blacklist the refresh token
            token.blacklist()
            
            return Response({
                'status': True,
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
            
        except KeyError:
            # Handle missing refresh token
            return Response({
                'status': False,
                'message': 'Refresh token not provided'
            }, status=status.HTTP_206_PARTIAL_CONTENT)
            
        except Exception as error:
            # Handle any unexpected errors
            return Response({
                'status': False,
                'message': 'An error occurred during logout',
                'error': str(error)
            }, status=status.HTTP_400_BAD_REQUEST)

class ChangePassword(APIView):
    """
    API View for changing user password. Accessible by any users.
    """
    permission_classes = (AllowAny,)

    def post(self, request):
        """
        Handle POST request for password change.

        Validates and updates the user's password.
        """
        try:
            # Attempt to serialize and validate password change data
            serializer = ChangePasswordSerializer(data=request.data)
            
            if serializer.is_valid():
                username = serializer.validated_data['username']
                password = serializer.validated_data['password']
                confirm_password = serializer.validated_data['confirm_password']

                try:
                    # Fetch the user by username
                    user = User.objects.get(username=username)
                    
                except User.DoesNotExist:
                    return Response({
                        'status': False,
                        'message': 'Invalid username'
                    }, status=status.HTTP_206_PARTIAL_CONTENT)

                # Verify password match
                if password != confirm_password:
                    return Response({
                        'status': False,
                        'message': 'Passwords do not match'
                    }, status=status.HTTP_206_PARTIAL_CONTENT)

                # Update the user's password
                user.set_password(confirm_password)
                user.save()

                return Response({
                    'status': True,
                    'message': 'Password changed successfully'
                }, status=status.HTTP_200_OK)
            else:
                # Return error if data is invalid
                return Response({
                    'status': False,
                    'message': 'Invalid data provided',
                    'errors': serializer.errors
                }, status=status.HTTP_206_PARTIAL_CONTENT)
                
        except Exception as e:
            # Handle any unexpected errors
            return Response({
                'status': False,
                'message': 'An error occurred while changing password',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
class UserProfile(APIView):
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        role = user.role
        data = {}

        if role == User.userRole.ADMIN:
            data = self.get_admin_dashboard_data(user)
        elif role == User.userRole.MANAGER:
            data = self.get_manager_dashboard_data(user)
        elif role == User.userRole.HR:
            data = self.get_hr_dashboard_data(user)
        else:  # USER
            data = self.get_user_dashboard_data(user)

        return Response({
            'status': True,
            'role': role,
            'data': data
        }, status=status.HTTP200_OK)

    def get_admin_dashboard_data(self, user):
        teams = Team.objects.filter(deleted_at__isnull=True).annotate(member_count=Count('members'))
        projects = Project.objects.filter(deleted_at__isnull=True).count()
        tasks = Task.objects.filter(deleted_at__isnull=True).count()
        return {
            'teams': [{'id': team.id, 'name': team.name, 'member_count': team.member_count} for team in teams],
            'total_projects': projects,
            'total_tasks': tasks
        }

    def get_manager_dashboard_data(self, user):
        teams = Team.objects.filter(members=user, deleted_at__isnull=True).annotate(
            task_count=Count('projects__tasks', filter=Q(projects__tasks__deleted_at__isnull=True))
        )
        return {
            'teams': [{'id': team.id, 'name': team.name, 'task_count': team.task_count} for team in teams]
        }

    def get_hr_dashboard_data(self, user):
        teams = Team.objects.filter(deleted_at__isnull=True).annotate(member_count=Count('members'))
        total_members = TeamMembersMapping.objects.filter(deleted_at__isnull=True).count()
        return {
            'teams': [{'id': team.id, 'name': team.name, 'member_count': team.member_count} for team in teams],
            'total_members': total_members
        }

    def get_user_dashboard_data(self, user):
        teams = Team.objects.filter(members=user, deleted_at__isnull=True).annotate(
            task_count=Count('projects__tasks', filter=Q(projects__tasks__deleted_at__isnull=True))
        )
        tasks_assigned = Task.objects.filter(assigned_to=user, deleted_at__isnull=True).count()
        return {
            'teams': [{'id': team.id, 'name': team.name, 'task_count': team.task_count} for team in teams],
            'tasks_assigned': tasks_assigned
        }
    

class UserList(APIView):
    permission_classes = (IsAuthenticated,)  # Or IsAdminUser if only admins can fetch users

    def post(self, request):
        role = request.query_params.get('role', None)
        users = User.objects.all()
        if role:
            users = users.filter(role=role)
        serializer = UserSerializer(users, many=True)
        return Response({
            'status': True,
            'count': users.count(),
            'records': serializer.data
        })

    # Optional: if you want to support POST as well
    def post(self, request):
        role = request.data.get('role', None)
        users = User.objects.all()
        if role:
            users = users.filter(role=role)
        serializer = UserSerializer(users, many=True)
        return Response({
            'status': True,
            'count': users.count(),
            'records': serializer.data
        })
    
class UserDetails(APIView):
    def get(self, request, id):
        try:
            employee = Employee.objects.select_related('user').filter(id=id).first()
            if not employee:
                return Response({'status': False, 'message': 'Not found'}, status=404)
            user = employee.user
            data = {
                'id': str(employee.id),
                'name': user.name,
                'designation': employee.designation,
                'salary': employee.salary,
                'date_of_joining': employee.date_of_joining,
                'date_of_birth': user.date_of_birth,
                'manager_name': None,  # adjust as needed
            }

            # Attendance records (Example: use your model fields)
            attendance = Attendance.objects.filter(employee=employee).order_by('-date')[:10]
            attendance_data = [{'date': a.date, 'in_time': a.in_time, 'out_time': a.out_time} for a in attendance]

            # Leave Requests
            leaves = LeaveRequest.objects.filter(employee=employee).order_by('-start_date')[:5]
            leave_data = [{'date': l.start_date, 'reason': l.reason, 'status': l.status} for l in leaves]

            return Response({
                'status': True,
                'records': data,
                'attendance': attendance_data,
                'leaves': leave_data,
            })

        except Exception as e:
            return Response({'status': False, 'error': str(e)}, status=400)
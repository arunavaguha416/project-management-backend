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
                    'message': 'Invalid credentials'
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
    permission_classes = (AllowAny,)

    def post(self, request):
        """
        Handle POST request for user registration. Creates a new user account and corresponding employee record.
        """
        try:
            # Create a mutable copy of request data
            data = request.data.copy()
            
            # Start a transaction to ensure both user and employee are created atomically
            with transaction.atomic():
                # Attempt to serialize and validate user data
                user_serializer = UserSerializer(data=data, partial=True)
                if not user_serializer.is_valid():
                    return Response({
                        'status': False,
                        'message': 'Invalid user data provided',
                        'errors': user_serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Save the new user
                user = user_serializer.save()
                
                # Prepare employee data
                employee_data = {
                    'user_id': str(user.id),
                    'company_id': data.get('comp_id'),
                    'department_id': data.get('dept_id'),
                    # 'phone': data.get('phone', '')
                }
                
                # Attempt to serialize and validate employee data
                employee_serializer = EmployeeSerializer(data=employee_data)
                if not employee_serializer.is_valid():
                    # Rollback user creation if employee data is invalid
                    return Response({
                        'status': False,
                        'message': 'Invalid employee data provided',
                        'errors': employee_serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Save the employee
                employee_serializer.save()
                
                return Response({
                    'status': True,
                    'message': 'User registered successfully',
                    'data': {
                        'user': user_serializer.data,
                        'employee': employee_serializer.data
                    }
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            # Handle any unexpected errors
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
        
class UserProfileView(APIView):
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
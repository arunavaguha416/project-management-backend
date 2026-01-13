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
from hr_management.models.hr_management_models import Employee, LeaveRequest, Attendance, LeaveBalance

from django.db.models import Count, Q

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
                    # phone=data.get('phone', '') # Uncomment if you want phone support
                )

                # NEW: Create LeaveBalance record with 20 days balance
                LeaveBalance.objects.create(
                    employee=employee,
                    balance=20  # Set default balance to 20 days
                )

                # Use serializer for Employee representation in response
                employee_data = EmployeeSerializer(employee).data

                return Response({
                    'status': True,
                    'message': 'User registered successfully with leave balance',
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


class CurrentUserRoleView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            user = request.user

            # Find employee linked to this user
            employee = Employee.objects.filter(
                user=user,
                deleted_at__isnull=True
            ).select_related('company').first()

            if not employee:
                return Response({
                    'status': False,
                    'message': 'Employee profile not found'
                }, status=404)

            return Response({
                'status': True,
                'data': {
                    'user_id': str(user.id),
                    'employee_id': str(employee.id),
                    'role': user.role,            # HR / MANAGER / EMPLOYEE
                    'is_admin': user.is_staff,
                    'company_id': str(employee.company_id) if employee.company_id else None
                }
            })

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Failed to fetch user role',
                'error': str(e)
            }, status=500)

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.db.models import Q
from teams.models.team_model import Team
from teams.models.team_members_mapping import TeamMembersMapping
from teams.serializers.team_serializer import TeamSerializer
from django.core.paginator import Paginator
import datetime
from hr_management.models.hr_management_models import Employee
from projects.models.project_model import Project, ManagerMapping, UserMapping
from authentication.models.user import User

class TeamAdd(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            serializer = TeamSerializer(data=request.data)
            if serializer.is_valid():
                team = serializer.save()
                member_ids = request.data.get('member_ids', [])
                project_ids = request.data.get('project_ids', [])
                if member_ids:
                    team.members.set(member_ids)
                if project_ids:
                    team.projects.set(project_ids)
                return Response({
                    'status': True,
                    'message': 'Team added successfully',
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
                'message': 'An error occurred while adding the team',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class TeamList(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)
            search_name = search_data.get('name', '')
            search_description = search_data.get('description', '')

            query = Q(members=request.user)
            if search_name:
                query &= Q(name__icontains=search_name)
            if search_description:
                query &= Q(description__icontains=search_description)

            teams = Team.objects.filter(query).order_by('-created_at')

            if teams.exists():
                if page is not None:
                    paginator = Paginator(teams, page_size)
                    paginated_teams = paginator.get_page(page)
                    serializer = TeamSerializer(paginated_teams, many=True)
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = TeamSerializer(teams, many=True)
                    return Response({
                        'status': True,
                        'count': teams.count(),
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Teams not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class DeletedTeamList(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)
            search_name = search_data.get('name', '')
            search_description = search_data.get('description', '')

            query = Q(deleted_at__isnull=False)
            if search_name:
                query &= Q(name__icontains=search_name)
            if search_description:
                query &= Q(description__icontains=search_description)

            teams = Team.all_objects.filter(query).order_by('-created_at')

            if teams.exists():
                if page is not None:
                    paginator = Paginator(teams, page_size)
                    paginated_teams = paginator.get_page(page)
                    serializer = TeamSerializer(paginated_teams, many=True)
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = TeamSerializer(teams, many=True)
                    return Response({
                        'status': True,
                        'count': teams.count(),
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Deleted teams not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class TeamDetails(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            team_id = request.data.get('id')
            if team_id:
                team = Team.objects.filter(
                    id=team_id, members=request.user
                ).values('id', 'name', 'description').first()
                if team:
                    return Response({
                        'status': True,
                        'records': team
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': False,
                        'message': 'Team not found or you are not a member',
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Please provide teamId'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching team details',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class TeamUpdate(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request):
        try:
            team_id = request.data.get('id')
            team = Team.objects.filter(id=team_id).first()
            if team:
                serializer = TeamSerializer(team, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    if 'member_ids' in request.data:
                        team.members.set(request.data.get('member_ids', []))
                    if 'project_ids' in request.data:
                        team.projects.set(request.data.get('project_ids', []))
                    return Response({
                        'status': True,
                        'message': 'Team updated successfully'
                    }, status=status.HTTP_200_OK)
                return Response({
                    'status': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'status': False,
                'message': 'Team not found'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while updating the team',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class TeamDelete(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request, team_id):
        try:
            team = Team.objects.filter(id=team_id).first()
            if team:
                team.soft_delete()
                return Response({
                    'status': True,
                    'message': 'Team deleted successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Team not found'
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class RestoreTeam(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            team_id = request.data.get('id')
            team = Team.all_objects.get(id=team_id)
            if team:
                team.deleted_at = None
                team.save()
                return Response({
                    'status': True,
                    'message': 'Team restored successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Team not found'
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        

class ManagerTeamMembers(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            employee = Employee.objects.filter(user=user).first()
            
            if not employee:
                return Response({
                    'status': False,
                    'message': 'Employee record not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            search_data = request.data
            page = int(search_data.get('page', 1))
            page_size = int(search_data.get('page_size', 10))
            search_term = search_data.get('search', '').strip()
            
            
            # Get teams for projects managed by this manager
            managed_projects = Project.objects.filter(manager=employee)
            
            # Get teams associated with managed projects
            teams_for_managed_projects = Team.objects.filter(
                project_id__in=managed_projects
            ).distinct()
            
            # Get team members from teams associated with managed projects
            team_members_query = User.objects.filter(
                teammembersmapping__team__in=teams_for_managed_projects
            ).distinct().select_related()
            
            # Apply search filter
            if search_term:
                team_members_query = team_members_query.filter(
                    Q(name__icontains=search_term) |
                    Q(email__icontains=search_term) |
                    Q(username__icontains=search_term)
                )
            
            team_members = team_members_query.order_by('name')
            
            if team_members.exists():
                paginator = Paginator(team_members, page_size)
                try:
                    paginated_members = paginator.page(page)
                except:
                    paginated_members = paginator.page(1)
                
                team_data = []
                for member in paginated_members:
                    # Get employee record for this user
                    member_employee = Employee.objects.filter(user=member).first()
                    
                    # Get teams this user belongs to under managed projects
                    user_teams = TeamMembersMapping.objects.filter(
                        user=member,
                        team__in=teams_for_managed_projects
                    ).select_related('team')
                    
                    # Get current active projects for this user
                    current_projects = []
                    for team_mapping in user_teams:
                        team_projects = team_mapping.team.project_id.filter(status='Ongoing')
                        current_projects.extend([proj.name for proj in team_projects])
                    
                    # Remove duplicates and join
                    current_projects = list(set(current_projects))
                    current_project_names = ', '.join(current_projects) if current_projects else 'No Active Project'
                    
                    member_info = {
                        'id': str(member.id),
                        'user_id': str(member.id),
                        'name': member.name,
                        'email': member.email,
                        'username': member.username,
                        'designation': member_employee.designation if member_employee else 'N/A',
                        'role': member.role,
                        'current_project': current_project_names,
                        'teams': [mapping.team.name for mapping in user_teams],
                        'status': 'Active' if current_projects else 'Available'
                    }
                    team_data.append(member_info)
                
                return Response({
                    'status': True,
                    'count': paginator.count,
                    'num_pages': paginator.num_pages,
                    'current_page': page,
                    'records': team_data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'No team members found',
                    'count': 0,
                    'records': []
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching team members',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ProjectTeamMembers(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            project_id = request.data.get('project_id')
            page_size = request.data.get('page_size', 20)
            
            if not project_id:
                return Response({
                    'status': False,
                    'message': 'Project ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get project
            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response({
                    'status': False,
                    'message': 'Project not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get team members through UserMapping
            team_mappings = UserMapping.objects.select_related(
                'employee__user',
                'employee__department',
                'employee__company'
            ).filter(project=project)
            
            # Apply pagination
            if page_size:
                team_mappings = team_mappings[:int(page_size)]
            
            # Get project manager through ManagerMapping
            manager_mapping = ManagerMapping.objects.select_related(
                'manager__user'
            ).filter(project=project).first()
            
            # Build team members data
            team_members = []
            for mapping in team_mappings:
                employee = mapping.employee
                team_members.append({
                    'mapping_id': str(mapping.id),
                    'id': str(employee.id),
                    'user_id': str(employee.user.id) if employee.user else None,
                    'name': employee.user.name if employee.user else 'Unknown',
                    'email': employee.user.email if employee.user else None,
                    'designation': employee.designation,
                    'department': employee.department.name if employee.department else None,
                    'company': employee.company.name if employee.company else None,
                    'role': 'Team Member',
                    'assigned_date': mapping.created_at.strftime('%Y-%m-%d') if mapping.created_at else None,
                    'join_date': mapping.created_at.strftime('%Y-%m-%d') if mapping.created_at else None
                })
            
            # Build manager info
            manager_info = None
            if manager_mapping and manager_mapping.manager:
                manager = manager_mapping.manager
                manager_info = {
                    'mapping_id': str(manager_mapping.id),
                    'id': str(manager.id),
                    'user_id': str(manager.user.id) if manager.user else None,
                    'name': manager.user.name if manager.user else 'Unknown',
                    'email': manager.user.email if manager.user else None,
                    'designation': manager.designation,
                    'department': manager.department.name if manager.department else None,
                    'company': manager.company.name if manager.company else None,
                    'role': 'Project Manager',
                    'assigned_date': manager_mapping.created_at.strftime('%Y-%m-%d') if manager_mapping.created_at else None
                }
            
            return Response({
                'status': True,
                'message': 'Project team retrieved successfully',
                'records': {
                    'project_id': str(project.id),
                    'project_name': project.name,
                    'project_status': project.status,
                    'manager': manager_info,
                    'team_members': team_members,
                    'team_size': len(team_members)
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching team members',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ManagerTeamMembers(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user

            # Resolve the manager as an Employee
            manager_employee = Employee.objects.filter(user=user).first()
            if not manager_employee:
                return Response({
                    'status': False,
                    'message': 'Employee record not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Inputs
            data = request.data or {}
            page = int(data.get('page', 1))
            page_size = int(data.get('page_size', 10))
            search_term = (data.get('search') or '').strip()

            # Projects managed by this manager (via ManagerMapping or direct manager field if present)
            managed_project_ids = set()

            # If your Project has a FK "manager" to Employee (as hinted in original code)
            direct_managed = Project.objects.filter(manager=manager_employee).values_list('id', flat=True)
            managed_project_ids.update(direct_managed)

            # Also include projects from ManagerMapping
            mapped_projects = ManagerMapping.objects.filter(manager=manager_employee).values_list('project_id', flat=True)
            managed_project_ids.update(mapped_projects)

            if not managed_project_ids:
                return Response({
                    'status': True,
                    'count': 0,
                    'num_pages': 0,
                    'current_page': 1,
                    'records': []
                }, status=status.HTTP_200_OK)

            # Get every user mapped to ANY of the managed projects through UserMapping
            # This represents "team members related to any project of a particular manager"
            user_ids_from_project_mapping = list(
                UserMapping.objects.filter(project_id__in=managed_project_ids)
                .values_list('employee__user_id', flat=True)
            )

            # Additionally, include users attached to Teams that are linked to managed projects
            # If your Team uses M2M 'project_id' to Project
            team_ids_for_projects = list(
                Team.objects.filter(project_id__in=managed_project_ids).values_list('id', flat=True)
            )
            user_ids_from_team_members = list(
                TeamMembersMapping.objects.filter(team_id__in=team_ids_for_projects)
                .values_list('user_id', flat=True)
            )

            # Combine both sources
            all_user_ids = set([uid for uid in user_ids_from_project_mapping if uid] + [uid for uid in user_ids_from_team_members if uid])

            # If nothing found, return empty list
            if not all_user_ids:
                return Response({
                    'status': True,
                    'count': 0,
                    'num_pages': 0,
                    'current_page': 1,
                    'records': []
                }, status=status.HTTP_200_OK)

            # Base query of users
            users_qs = User.objects.filter(id__in=all_user_ids).distinct()

            # Optional search across common fields
            if search_term:
                users_qs = users_qs.filter(
                    Q(name__icontains=search_term) |
                    Q(email__icontains=search_term) |
                    Q(username__icontains=search_term)
                )

            # Order by name for predictability
            users_qs = users_qs.order_by('name')

            # Paginate
            paginator = Paginator(users_qs, page_size)
            try:
                page_obj = paginator.page(page)
            except Exception:
                page_obj = paginator.page(1)

            # Build records
            records = []
            user_list = list(page_obj.object_list)

            # Pre-fetch helpful structures to avoid N+1
            # For each user, we will compute:
            # - designation (from Employee)
            # - teams (names under managed projects)
            # - current active projects (Project.status == 'Ongoing') under managed projects

            # Map user_id -> Employee for quick lookup
            employees_by_user = {
                e.user_id: e
                for e in Employee.objects.filter(user_id__in=[u.id for u in user_list])
            }

            # Teams under managed projects
            teams_under_managed = Team.objects.filter(project_id__in=managed_project_ids)

            # TeamMemberships for users within these teams
            memberships = TeamMembersMapping.objects.filter(
                user_id__in=[u.id for u in user_list],
                team_id__in=teams_under_managed.values_list('id', flat=True)
            ).select_related('team')

            # Build map: user_id -> set of team names
            teams_by_user = {}
            for m in memberships:
                teams_by_user.setdefault(m.user_id, set()).add(m.team.name)

            # User-to-projects via UserMapping limited to managed projects
            mappings = UserMapping.objects.filter(
                employee__user_id__in=[u.id for u in user_list],
                project_id__in=managed_project_ids
            ).select_related('project', 'employee__user')

            # Build map: user_id -> list of their active ("Ongoing") projects under managed projects
            active_projects_by_user = {}
            for mp in mappings:
                if getattr(mp.project, 'status', None) == 'Ongoing':
                    active_projects_by_user.setdefault(mp.employee.user_id, set()).add(mp.project.name)

            # Final record assembly
            for u in user_list:
                emp = employees_by_user.get(u.id)
                team_names = sorted(list(teams_by_user.get(u.id, set())))
                active_projects = sorted(list(active_projects_by_user.get(u.id, set())))
                current_project_names = ', '.join(active_projects) if active_projects else 'No Active Project'

                records.append({
                    'id': str(u.id),
                    'user_id': str(u.id),
                    'name': u.name,
                    'email': u.email,
                    'username': u.username,
                    'designation': getattr(emp, 'designation', 'N/A'),
                    'role': u.role,
                    'current_project': current_project_names,
                    'teams': team_names,
                    'status': 'Active' if active_projects else 'Available',
                })

            return Response({
                'status': True,
                'count': paginator.count,
                'num_pages': paginator.num_pages,
                'current_page': page_obj.number,
                'records': records
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching team members',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        

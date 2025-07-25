from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.db.models import Q
from teams.models.team_model import Team
from teams.serializers.team_serializer import TeamSerializer
from django.core.paginator import Paginator
import datetime

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
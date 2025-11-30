from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.db.models import Q
from projects.models.sprint_model import Sprint
from projects.models.project_model import Project
from projects.models.task_model import Task
from projects.models.comments_model import Comment
from projects.serializers.sprint_serializer import SprintSerializer
from django.core.paginator import Paginator
from django.db.models import Q, Case, When, Value, IntegerField, F, Count
from django.utils import timezone

class SprintList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)
            search_name = search_data.get('name', '')
            search_description = search_data.get('description', '')

            query = Q(projects__company__id=search_data.get('company_id', '')) if search_data.get('company_id') else Q()
            if search_name:
                query &= Q(name__icontains=search_name)
            if search_description:
                query &= Q(description__icontains=search_description)

            sprints = Sprint.objects.filter(query).order_by('-created_at')

            if sprints.exists():
                if page is not None:
                    paginator = Paginator(sprints, page_size)
                    paginated_sprints = paginator.get_page(page)
                    serializer = SprintSerializer(paginated_sprints, many=True)
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = SprintSerializer(sprints, many=True)
                    return Response({
                        'status': True,
                        'count': sprints.count(),
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Sprints not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class SprintDetails(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get('id')
            if sprint_id:
                sprint = Sprint.objects.filter(id=sprint_id).values(
                    'id', 'name', 'description', 'start_date', 'end_date', 'project__id', 'project__name'
                ).first()
                if sprint:
                    return Response({
                        'status': True,
                        'records': sprint
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': False,
                        'message': 'Sprint not found',
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Please provide sprintId'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching sprint details',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class SprintUpdate(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        try:
            sprint_id = request.data.get('id')
            sprint = Sprint.objects.filter(id=sprint_id).first()
            if sprint:
                serializer = SprintSerializer(sprint, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'status': True,
                        'message': 'Sprint updated successfully'
                    }, status=status.HTTP_200_OK)
                return Response({
                    'status': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'status': False,
                'message': 'Sprint not found'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while updating the sprint',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class SprintDelete(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, sprint_id):
        try:
            sprint = Sprint.objects.filter(id=sprint_id).first()
            if sprint:
                sprint.soft_delete()
                return Response({
                    'status': True,
                    'message': 'Sprint deleted successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Sprint not found'
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class RestoreSprint(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get('id')
            sprint = Sprint.all_objects.get(id=sprint_id)
            if sprint:
                sprint.deleted_at = None
                sprint.save()
                return Response({
                    'status': True,
                    'message': 'Sprint restored successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Sprint not found'
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class AddProjectToSprint(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get('sprint_id')
            project_id = request.data.get('project_id')
            sprint = Sprint.objects.filter(id=sprint_id).first()
            project = Project.objects.filter(id=project_id).first()
            if sprint and project:
                sprint.projects.add(project)
                return Response({
                    'status': True,
                    'message': 'Project added to sprint successfully'
                }, status=status.HTTP_200_OK)
            return Response({
                'status': False,
                'message': 'Sprint or project not found'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class RemoveProjectFromSprint(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get('sprint_id')
            project_id = request.data.get('project_id')
            sprint = Sprint.objects.filter(id=sprint_id).first()
            project = Project.objects.filter(id=project_id).first()
            if sprint and project:
                sprint.projects.remove(project)
                return Response({
                    'status': True,
                    'message': 'Project removed from sprint successfully'
                }, status=status.HTTP_200_OK)
            return Response({
                'status': False,
                'message': 'Sprint or project not found'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
class SprintSummary(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get('id')
            if not sprint_id:
                return Response({
                    'status': False,
                    'message': 'Please provide sprintId'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Fetch sprint with related projects
            sprint = Sprint.objects.filter(id=sprint_id).first()
            if not sprint:
                return Response({
                    'status': False,
                    'message': 'Sprint not found'
                }, status=status.HTTP_200_OK)

            # Serialize sprint details
            sprint_serializer = SprintSerializer(sprint)

            # Aggregate task counts by status
            task_counts = Task.objects.filter(sprint__id=sprint_id).aggregate(
                total_tasks=Count('id'),
                todo_tasks=Count('id', filter=Q(status='TODO')),
                in_progress_tasks=Count('id', filter=Q(status='IN_PROGRESS')),
                done_tasks=Count('id', filter=Q(status='DONE'))
            )

            # Optional: Count comments for tasks in this sprint
            comment_count = Comment.objects.filter(task__sprint__id=sprint_id).count()

            # Build summary response
            summary = {
                'sprint': sprint_serializer.data,
                'task_summary': {
                    'total_tasks': task_counts['total_tasks'],
                    'todo_tasks': task_counts['todo_tasks'],
                    'in_progress_tasks': task_counts['in_progress_tasks'],
                    'done_tasks': task_counts['done_tasks']
                },
                'comment_count': comment_count
            }

            return Response({
                'status': True,
                'records': summary
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching sprint summary',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
class CurrentSprint(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project_id = request.data.get('project_id')
            if not project_id:
                return Response({
                    'status': False,
                    'message': 'Please provide project_id'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Prefer ACTIVE sprint; else PLANNED; else latest by date/created
            s = (Sprint.objects
                 .filter(project__id=project_id)
                 .order_by(
                     # ACTIVE first, then PLANNED, then COMPLETED
                     # then latest by start_date/created_at
                     # Use simple ordering by status priority mapping
                 ))

            # Simple priority: ACTIVE > PLANNED > COMPLETED
            priority_map = {'ACTIVE': 0, 'PLANNED': 1, 'COMPLETED': 2}
            sprint = None
            for sp in s:
                if sprint is None:
                    sprint = sp
                else:
                    if priority_map.get(sp.status, 99) < priority_map.get(sprint.status, 99):
                        sprint = sp

            if not sprint:
                return Response({'status': True, 'records': None}, status=status.HTTP_200_OK)

            data = {
                'id': str(sprint.id),
                'name': sprint.name,
                'status': sprint.status,
                'start_date': sprint.start_date,
                'end_date': sprint.end_date,
                'initials': sprint.initials if hasattr(sprint, 'initials') else None
            }
            return Response({'status': True, 'records': data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching current sprint',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class SprintStart(APIView):
    """
    Enhanced start sprint logic:
    - If there is an ACTIVE sprint for the project, do NOT start a new one. Return message to complete it first.
    - If sprint_id or an existing PLANNED sprint is provided/found, start it.
    - If no sprint_id/PLANNED sprint and no ACTIVE sprint:
        - Require 'initials' on first ever sprint for the project. Persist to future sprints by reading from the last sprint created for that project.
        - Auto-generate the next sprint name: "{INITIALS} Sprint {N}" where N = 1 + max existing sprint number for that initials/project.
        - Create the sprint with status ACTIVE.
    Request payload:
        {
          "project_id": "<uuid>",
          "sprint_id": "<uuid|null>",
          "initials": "USA"   # only needed on first sprint for a project
          "start_date": "YYYY-MM-DD" (optional)
          "end_date": "YYYY-MM-DD" (optional)
        }
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project_id = request.data.get('project_id')
            sprint_id = request.data.get('sprint_id')
            initials_in = (request.data.get('initials') or '').strip().upper()
            start_date = request.data.get('start_date')
            end_date = request.data.get('end_date')

            if not project_id:
                return Response({'status': False, 'message': 'project_id is required'}, status=status.HTTP_400_BAD_REQUEST)

            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response({'status': False, 'message': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

            # 1) If an ACTIVE sprint exists, block starting a new one.
            active_sprint = Sprint.objects.filter(project=project, status='ACTIVE').first()
            if active_sprint:
                return Response({
                    'status': False,
                    'message': 'A sprint is already ACTIVE. Complete the current sprint before starting a new one.',
                    'records': {
                        'id': str(active_sprint.id),
                        'name': active_sprint.name,
                        'status': active_sprint.status
                    }
                }, status=status.HTTP_200_OK)

            # 2) If a specific sprint_id is provided, start that sprint.
            if sprint_id:
                sp = Sprint.objects.filter(id=sprint_id, project=project).first()
                if not sp:
                    return Response({'status': False, 'message': 'Sprint not found for this project'}, status=status.HTTP_200_OK)
                sp.status = 'ACTIVE'
                if start_date:
                    sp.start_date = start_date
                if end_date:
                    sp.end_date = end_date
                sp.save()
                return Response({'status': True, 'message': 'Sprint started successfully', 'records': {'id': str(sp.id), 'name': sp.name}}, status=status.HTTP_200_OK)

            # 3) If there's a PLANNED sprint, start the earliest PLANNED one.
            planned = Sprint.objects.filter(project=project, status='PLANNED').order_by('start_date', 'created_at').first()
            if planned:
                planned.status = 'ACTIVE'
                if start_date:
                    planned.start_date = start_date
                if end_date:
                    planned.end_date = end_date
                planned.save()
                return Response({'status': True, 'message': 'Sprint started successfully', 'records': {'id': str(planned.id), 'name': planned.name}}, status=status.HTTP_200_OK)

            # 4) No ACTIVE or PLANNED sprint -> create and start a new sprint with predictable naming
            # Determine initials to use:
            # - Prefer provided initials
            # - Else check last sprint's initials for this project
            last_project_sprint = Sprint.objects.filter(project=project).order_by('-created_at').first()
            if last_project_sprint and getattr(last_project_sprint, 'initials', None):
                effective_initials = last_project_sprint.initials
            else:
                # First time: must provide initials
                if not initials_in:
                    return Response({
                        'status': False,
                        'message': 'Initials are required to start the first sprint for this project.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                effective_initials = initials_in

            # Determine next sprint number for these initials on this project
            # Expect names formatted as "{INITIALS} Sprint {N}"
            existing_names = Sprint.objects.filter(project=project, name__istartswith=f"{effective_initials} Sprint ").values_list('name', flat=True)
            max_num = 0
            for nm in existing_names:
                try:
                    # parse trailing number
                    parts = nm.strip().split()
                    num = int(parts[-1])
                    max_num = max(max_num, num)
                except Exception:
                    continue
            next_num = max_num + 1
            next_name = f"{effective_initials} Sprint {next_num}"

            # Create ACTIVE sprint
            sp_new = Sprint.objects.create(
                project=project,
                name=next_name,
                description=f"Auto-created sprint {next_num} for {effective_initials}",
                start_date=start_date or timezone.now().date(),
                end_date=end_date,
                status='ACTIVE',
                # Store initials if the model has the field; ignore otherwise
                **({'initials': effective_initials} if 'initials' in [f.name for f in Sprint._meta.get_fields()] else {})
            )

            return Response({
                'status': True,
                'message': 'Sprint created and started successfully',
                'records': {'id': str(sp_new.id), 'name': sp_new.name, 'initials': effective_initials}
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while starting the sprint',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class SprintEnd(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get('sprint_id')
            if not sprint_id:
                return Response({
                    'status': False,
                    'message': 'Please provide sprint_id'
                }, status=status.HTTP_400_BAD_REQUEST)

            sprint = Sprint.objects.filter(id=sprint_id).first()
            if not sprint:
                return Response({'status': False, 'message': 'Sprint not found'}, status=status.HTTP_200_OK)

            sprint.status = 'COMPLETED'
            sprint.save()

            return Response({'status': True, 'message': 'Sprint completed successfully'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while completing the sprint',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
class BacklogForSprint(APIView):
    """
    POST payload:
    {
      "sprint_id": "<uuid>",
      "title": "<optional search title>",
      "description": "<optional search description>",
      "page_size": <optional int, default 50>
    }

    Returns backlog tasks for the sprint's project (tasks with sprint IS NULL).
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get('sprint_id')
            if not sprint_id:
                return Response({'status': False, 'message': 'Please provide sprint_id'}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch sprint
            sprint = Sprint.objects.filter(id=sprint_id).select_related('project').first()
            if not sprint:
                return Response({'status': False, 'message': 'Sprint not found'}, status=status.HTTP_200_OK)

            # Optional filters
            search_title = (request.data.get('title') or '').strip()
            search_description = (request.data.get('description') or '').strip()
            page_size = int(request.data.get('page_size', 50))

            # Build query: same project, sprint is NULL -> backlog for that project/sprint
            query = Q(project=sprint.project, sprint__isnull=True)
            if search_title:
                query &= Q(title__icontains=search_title)
            if search_description:
                query &= Q(description__icontains=search_description)

            # Select related to avoid N+1
            tasks_qs = Task.objects.filter(query).select_related('project', 'assigned_to').order_by('-created_at')

            # Limit by page_size
            if page_size:
                tasks_qs = tasks_qs[:page_size]

            if not tasks_qs.exists():
                return Response({'status': False, 'message': 'Backlog tasks not found'}, status=status.HTTP_200_OK)

            records = []
            for t in tasks_qs:
                # compute assignee name safely
                assignee_name = 'Unassigned'
                if getattr(t, 'assigned_to', None):
                    # assigned_to may be Employee or User depending on your auth model
                    if hasattr(t.assigned_to, 'user') and getattr(t.assigned_to.user, 'name', None):
                        assignee_name = t.assigned_to.user.name
                    elif getattr(t.assigned_to, 'name', None):
                        assignee_name = t.assigned_to.name
                    elif getattr(t.assigned_to, 'username', None):
                        assignee_name = t.assigned_to.username

                due_date_str = None
                if getattr(t, 'due_date', None):
                    try:
                        due_date_str = t.due_date.strftime('%Y-%m-%d')
                    except Exception:
                        # If due_date is datetime-like with .date()
                        try:
                            due_date_str = t.due_date.date().strftime('%Y-%m-%d')
                        except Exception:
                            due_date_str = None

                records.append({
                    'id': str(t.id),
                    'title': t.title,
                    'name': t.title,
                    'description': t.description or '',
                    'status': t.status,
                    'priority': getattr(t, 'priority', 'MEDIUM'),
                    'assignee_name': assignee_name,
                    'assigned_to_id': str(t.assigned_to.id) if getattr(t, 'assigned_to', None) else None,
                    'due_date': due_date_str,
                    'created_at': t.created_at.strftime('%Y-%m-%d %H:%M:%S') if getattr(t, 'created_at', None) else None,
                    'updated_at': t.updated_at.strftime('%Y-%m-%d %H:%M:%S') if getattr(t, 'updated_at', None) else None,
                    'project_id': str(t.project.id) if getattr(t, 'project', None) else None,
                    'project_name': t.project.name if getattr(t, 'project', None) else None,
                    # sprint fields are null (backlog)
                    'sprint_id': None,
                    'sprint_name': None,
                })

            return Response({'status': True, 'count': len(records), 'records': records}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': 'An error occurred while fetching backlog tasks', 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ProjectSprints(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """
        POST payload:
        { "project_id": "<uuid>" }

        Returns sprints for project ordered by start_date desc
        """
        try:
            project_id = request.data.get('project_id')
            if not project_id:
                return Response({'status': False, 'message': 'project_id is required'}, status=status.HTTP_400_BAD_REQUEST)

            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response({'status': False, 'message': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

            sprints = Sprint.objects.filter(project=project).order_by('-start_date', '-created_at')
            if not sprints.exists():
                return Response({'status': False, 'message': 'Sprints not found', 'records': []}, status=status.HTTP_200_OK)

            records = []
            for s in sprints:
                records.append({
                    'id': str(s.id),
                    'name': s.name,
                    'status': s.status,
                    'start_date': s.start_date.strftime('%Y-%m-%d') if getattr(s, 'start_date', None) else None,
                    'end_date': s.end_date.strftime('%Y-%m-%d') if getattr(s, 'end_date', None) else None,
                })

            return Response({'status': True, 'count': len(records), 'records': records}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)








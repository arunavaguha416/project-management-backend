from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Sum, Q

from projects.models.sprint_model import Sprint
from projects.models.task_model import Task
from projects.models.task_model import TaskStatusHistory
from projects.utils.permissions import require_project_viewer
from datetime import timedelta



class SprintSummaryReport(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get('sprint_id')

            sprint = Sprint.objects.select_related('project').filter(id=sprint_id).first()
            if not sprint:
                return Response(
                    {'status': False, 'message': 'Sprint not found'},
                    status=status.HTTP_200_OK
                )

            # 🔐 permission
            require_project_viewer(request.user, sprint.project)

            tasks = Task.objects.filter(
                sprint=sprint,
                deleted_at__isnull=True
            )

            total_tasks = tasks.count()
            completed_tasks = tasks.filter(status='DONE').count()
            remaining_tasks = total_tasks - completed_tasks

            total_story_points = tasks.aggregate(
                total=Sum('story_points')
            )['total'] or 0

            completed_story_points = tasks.filter(
                status='DONE'
            ).aggregate(
                total=Sum('story_points')
            )['total'] or 0

            status_breakdown = {
                row['status']: row['count']
                for row in tasks.values('status')
                .annotate(count=Count('id'))
            }

            return Response({
                'status': True,
                'records': {
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'remaining_tasks': remaining_tasks,
                    'total_story_points': total_story_points,
                    'completed_story_points': completed_story_points,
                    "ai_completion_probability": sprint.ai_completion_probability,
                    'status_breakdown': status_breakdown
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class SprintAssigneeReport(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get('sprint_id')

            sprint = Sprint.objects.select_related('project').filter(id=sprint_id).first()
            if not sprint:
                return Response(
                    {'status': False, 'message': 'Sprint not found'},
                    status=status.HTTP_200_OK
                )

            require_project_viewer(request.user, sprint.project)

            rows = (
                Task.objects
                .filter(sprint=sprint, deleted_at__isnull=True)
                .values(
                    'assigned_to__id',
                    'assigned_to__name'
                )
                .annotate(
                    task_count=Count('id'),
                    story_points=Sum('story_points')
                )
            )

            records = [{
                'assignee_id': r['assigned_to__id'],
                'assignee_name': r['assigned_to__name'] or 'Unassigned',
                'tasks': r['task_count'],
                'story_points': r['story_points'] or 0
            } for r in rows]

            return Response({
                'status': True,
                'records': records
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class SprintSpilloverReport(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get('sprint_id')

            sprint = Sprint.objects.select_related('project').filter(id=sprint_id).first()
            if not sprint:
                return Response(
                    {'status': False, 'message': 'Sprint not found'},
                    status=status.HTTP_200_OK
                )

            require_project_viewer(request.user, sprint.project)

            spillover_tasks = TaskStatusHistory.objects.filter(
                sprint=sprint,
                action='SPRINT_SPILLOVER'
            ).select_related('task')

            records = [{
                'task_id': h.task.id,
                'title': h.task.title,
                'previous_status': h.from_status,
                'current_status': h.to_status,
                'story_points': h.task.story_points
            } for h in spillover_tasks]

            return Response({
                'status': True,
                'records': records
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class SprintBurndownView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get('sprint_id')
            if not sprint_id:
                return Response({'status': False, 'message': 'sprint id is required'},
                                status=status.HTTP_400_BAD_REQUEST)
            
            sprint = Sprint.objects.select_related('project').filter(id=sprint_id).first()
            if not sprint:
                return Response({'status': False, 'message': 'Sprint not found'}, status=200)

            require_project_viewer(request.user, sprint.project)

            if not sprint.start_date or not sprint.end_date:
                return Response({'status': True, 'records': []}, status=200)

            tasks = Task.objects.filter(
                sprint=sprint,
                deleted_at__isnull=True
            )

            total_points = tasks.aggregate(
                total=Sum('story_points')
            )['total'] or 0

            records = []
            current_date = sprint.start_date

            while current_date <= sprint.end_date:
                completed_points = TaskStatusHistory.objects.filter(
                    sprint=sprint,
                    to_status='DONE',
                    created_at__date__lte=current_date
                ).aggregate(
                    total=Sum('task__story_points')
                )['total'] or 0

                records.append({
                    'date': current_date,
                    'remaining_story_points': max(total_points - completed_points, 0)
                })

                current_date += timedelta(days=1)

            return Response({'status': True, 'records': records}, status=200)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=400)
        




class SprintVelocityView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get('sprint_id')
            if not sprint_id:
                return Response({'status': False, 'message': 'sprint id is required'},
                                status=status.HTTP_400_BAD_REQUEST)
            
            sprint = Sprint.objects.select_related('project').filter(id=sprint_id).first()
            if not sprint:
                return Response({'status': False, 'message': 'Sprint not found'}, status=200)

            require_project_viewer(request.user, sprint.project)

            completed_story_points = Task.objects.filter(
                sprint=sprint,
                status='DONE',
                deleted_at__isnull=True
            ).aggregate(
                total=Sum('story_points')
            )['total'] or 0

            return Response({
                'status': True,
                'records': {
                    'completed_story_points': completed_story_points
                }
            }, status=200)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=400)
        



class SprintScopeChangeView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get('sprint_id')
            if not sprint_id:
                return Response(
                    {'status': False, 'message': 'sprint id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            sprint = Sprint.objects.select_related('project').filter(id=sprint_id).first()
            if not sprint:
                return Response({'status': False, 'message': 'Sprint not found'}, status=200)

            require_project_viewer(request.user, sprint.project)

            # Task moved INTO sprint (Backlog -> Sprint status)
            added = TaskStatusHistory.objects.filter(
                task__sprint=sprint,
                from_status='BACKLOG'
            ).exclude(
                to_status='BACKLOG'
            ).count()

            # Task moved OUT of sprint (Sprint status -> Backlog)
            removed = TaskStatusHistory.objects.filter(
                task__sprint=sprint,
                to_status='BACKLOG'
            ).exclude(
                from_status='BACKLOG'
            ).count()

            return Response({
                'status': True,
                'records': {
                    'added': added,
                    'removed': removed,
                    'net': added - removed
                }
            }, status=200)

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )



class SprintAssigneeWorkloadView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get('sprint_id')
            if not sprint_id:
                return Response({'status': False, 'message': 'sprint id is required'},
                                status=status.HTTP_400_BAD_REQUEST)
            
            sprint = Sprint.objects.select_related('project').filter(id=sprint_id).first()
            if not sprint:
                return Response({'status': False, 'message': 'Sprint not found'}, status=200)

            require_project_viewer(request.user, sprint.project)

            rows = (
                Task.objects
                .filter(sprint=sprint, deleted_at__isnull=True)
                .values('assigned_to__name')
                .annotate(
                    tasks=Count('id'),
                    story_points=Sum('story_points')
                )
            )

            records = [{
                'assignee': r['assigned_to__name'] or 'Unassigned',
                'tasks': r['tasks'],
                'story_points': r['story_points'] or 0
            } for r in rows]

            return Response({'status': True, 'records': records}, status=200)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=400)
        




class SprintStatusBreakdownReport(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get('sprint_id')
            if not sprint_id:
                return Response({'status': False, 'message': 'sprint id is required'},
                                status=status.HTTP_400_BAD_REQUEST)
            
            sprint = Sprint.objects.select_related('project').filter(id=sprint_id).first()
            if not sprint:
                return Response({'status': False, 'message': 'Sprint not found'}, status=200)

            require_project_viewer(request.user, sprint.project)

            rows = (
                Task.objects
                .filter(sprint=sprint, deleted_at__isnull=True)
                .values('status')
                .annotate(count=Count('id'))
            )

            records = [{
                'status': r['status'],
                'count': r['count']
            } for r in rows]

            return Response({'status': True, 'records': records}, status=200)

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        



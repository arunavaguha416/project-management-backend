from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from projects.models.ai_models import AIInsight
from projects.models.project_model import Project
from projects.models.task_model import Task
from django.db.models import Count, Avg
from datetime import datetime, timedelta

class ProjectAIInsights(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, project_id):
        """Get AI insights for a project"""
        try:
            project = Project.objects.get(id=project_id)
            insights = project.ai_insights.filter(is_active=True).order_by('-created_at')[:10]
            
            insights_data = [{
                'id': str(insight.id),
                'type': insight.insight_type,
                'title': insight.title,
                'description': insight.description,
                'confidence_score': insight.confidence_score,
                'data': insight.data,
                'created_at': insight.created_at
            } for insight in insights]
            
            return Response({
                'status': True,
                'insights': insights_data
            })
            
        except Project.DoesNotExist:
            return Response({
                'status': False,
                'message': 'Project not found'
            }, status=status.HTTP_404_NOT_FOUND)

class GenerateProjectHealthScore(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, project_id):
        """Generate AI health score for project"""
        try:
            project = Project.objects.get(id=project_id)
            
            # Simple AI calculation based on task completion rates
            total_tasks = project.tasks.count()
            completed_tasks = project.tasks.filter(status='DONE').count()
            overdue_tasks = project.tasks.filter(
                due_date__lt=datetime.now(),
                status__in=['TODO', 'IN_PROGRESS']
            ).count()
            
            if total_tasks == 0:
                health_score = 50  # Neutral score for new projects
            else:
                completion_rate = completed_tasks / total_tasks
                overdue_penalty = min(0.3, overdue_tasks / total_tasks)
                health_score = max(0, min(100, int((completion_rate - overdue_penalty) * 100)))
            
            project.ai_health_score = health_score
            project.save()
            
            # Create insight record
            AIInsight.objects.create(
                project=project,
                insight_type='SPRINT_HEALTH',
                title=f'Project Health Score: {health_score}%',
                description=f'Based on {completion_rate:.1%} completion rate and {overdue_tasks} overdue tasks',
                confidence_score=85,
                data={'completion_rate': completion_rate, 'overdue_tasks': overdue_tasks}
            )
            
            return Response({
                'status': True,
                'health_score': health_score,
                'message': 'Health score updated successfully'
            })
            
        except Project.DoesNotExist:
            return Response({
                'status': False,
                'message': 'Project not found'
            }, status=status.HTTP_404_NOT_FOUND)

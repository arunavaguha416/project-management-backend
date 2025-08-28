import os
import re
from datetime import datetime, timedelta
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser

from projects.models.project_model import Project
from projects.models.task_model import Task  
from authentication.models.user import User
from ai_insights.models.ai_models import AIRecommendation, ProjectHealthMetric

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

class SecureAIDataService:
    """Secure service to provide AI with sanitized database access"""
    
    def __init__(self, user):
        self.user = user
        self.role = getattr(user, 'role', 'GUEST') if user and not isinstance(user, AnonymousUser) else 'GUEST'
    
    def get_projects_data(self):
        """Get sanitized project data based on user role"""
        try:
            if self.role == 'HR':
                projects = Project.objects.all()
            elif self.role == 'MANAGER':
                projects = Project.objects.filter(
                    Q(created_by=self.user) | Q(manager=self.user)
                )
            else:
                # Employee access - only projects they're assigned to
                projects = Project.objects.filter(
                    Q(created_by=self.user) | 
                    Q(tasks__assigned_to=self.user)
                ).distinct()
            
            # Sanitize project data
            project_data = []
            for project in projects.order_by('-created_at')[:15]:  # Limit to 15 recent
                project_info = {
                    'name': project.name,
                    'status': project.status,
                    'progress': getattr(project, 'progress', 0),
                    'priority': getattr(project, 'priority', 'medium'),
                    'created_date': project.created_at.strftime('%Y-%m-%d') if project.created_at else None,
                    'task_count': project.tasks.count() if hasattr(project, 'tasks') else 0,
                    'team_size': self._get_project_team_size(project),
                    'is_active': project.status in ['Ongoing', 'Active'],
                }
                project_data.append(project_info)
            
            return {
                'total_projects': projects.count(),
                'active_projects': projects.filter(status__in=['Ongoing', 'Active']).count(),
                'completed_projects': projects.filter(status='Completed').count(),
                'project_details': project_data
            }
        except Exception as e:
            return {'error': str(e), 'total_projects': 0}
    
    def get_tasks_data(self):
        """Get sanitized task data"""
        try:
            if self.role == 'HR':
                tasks = Task.objects.all()
            elif self.role == 'MANAGER':
                tasks = Task.objects.filter(
                    Q(project__created_by=self.user) |
                    Q(project__manager=self.user)
                )
            else:
                tasks = Task.objects.filter(assigned_to=self.user)
            
            # Task summary statistics
            task_summary = {
                'total_tasks': tasks.count(),
                'todo_tasks': tasks.filter(status='TODO').count(),
                'in_progress_tasks': tasks.filter(status='IN_PROGRESS').count(),
                'completed_tasks': tasks.filter(status='DONE').count(),
                'blocked_tasks': tasks.filter(status='BLOCKED').count(),
                'high_priority_tasks': tasks.filter(priority='HIGH').count(),
                'overdue_tasks': self._get_overdue_tasks_count(tasks),
            }
            
            # Recent tasks (non-sensitive info only)
            recent_tasks = []
            for task in tasks.order_by('-created_at')[:10]:
                task_info = {
                    'title': task.title,
                    'status': task.status,
                    'priority': getattr(task, 'priority', 'MEDIUM'),
                    'project_name': task.project.name if task.project else None,
                    'assigned_to': task.assigned_to.get_full_name() if task.assigned_to else 'Unassigned',
                    'due_date': task.due_date.strftime('%Y-%m-%d') if hasattr(task, 'due_date') and task.due_date else None,
                }
                recent_tasks.append(task_info)
            
            task_summary['recent_tasks'] = recent_tasks
            return task_summary
        except Exception as e:
            return {'error': str(e), 'total_tasks': 0}
    
    def get_team_data(self):
        """Get team statistics (role-based access)"""
        try:
            if self.role not in ['HR', 'MANAGER']:
                return {'access_denied': True, 'message': 'Limited team access for your role'}
            
            if self.role == 'HR':
                users = User.objects.filter(is_active=True)
            else:
                # Manager can see team members from their projects
                users = User.objects.filter(
                    Q(tasks__project__created_by=self.user) |
                    Q(tasks__project__manager=self.user),
                    is_active=True
                ).distinct()
            
            team_stats = {
                'total_members': users.count(),
                'managers': users.filter(role='MANAGER').count(),
                'employees': users.filter(role='EMPLOYEE').count(),
                'hr_members': users.filter(role='HR').count() if self.role == 'HR' else 0,
                'active_members': users.filter(is_active=True).count(),
            }
            
            # Team composition (anonymized)
            team_composition = []
            for role in ['HR', 'MANAGER', 'EMPLOYEE']:
                role_count = users.filter(role=role).count()
                if role_count > 0:
                    team_composition.append({
                        'role': role,
                        'count': role_count,
                        'percentage': round((role_count / users.count()) * 100, 1) if users.count() > 0 else 0
                    })
            
            team_stats['team_composition'] = team_composition
            return team_stats
        except Exception as e:
            return {'error': str(e)}
    
    def get_ai_recommendations_summary(self):
        """Get AI recommendations summary"""
        try:
            if self.role == 'HR':
                recommendations = AIRecommendation.objects.all()
            elif self.role == 'MANAGER':
                recommendations = AIRecommendation.objects.filter(
                    Q(created_by=self.user) |
                    Q(project__created_by=self.user) |
                    Q(project__manager=self.user)
                )
            else:
                recommendations = AIRecommendation.objects.filter(created_by=self.user)
            
            rec_stats = {
                'total_recommendations': recommendations.count(),
                'applied_recommendations': recommendations.filter(is_applied=True).count(),
                'pending_recommendations': recommendations.filter(is_applied=False).count(),
                'high_impact_recs': recommendations.filter(impact='high').count(),
                'recent_count': recommendations.filter(
                    created_at__gte=timezone.now() - timedelta(days=7)
                ).count(),
            }
            
            # Recent recommendations (sanitized)
            recent_recs = []
            for rec in recommendations.order_by('-created_at')[:5]:
                rec_info = {
                    'title': rec.title,
                    'type': rec.recommendation_type,
                    'impact': rec.impact,
                    'confidence': rec.confidence,
                    'is_applied': rec.is_applied,
                    'project_name': rec.project.name if rec.project else None,
                    'created_date': rec.created_at.strftime('%Y-%m-%d') if rec.created_at else None,
                }
                recent_recs.append(rec_info)
            
            rec_stats['recent_recommendations'] = recent_recs
            return rec_stats
        except Exception as e:
            return {'error': str(e)}
    
    def get_system_metrics(self):
        """Get overall system health metrics"""
        try:
            current_date = timezone.now()
            last_week = current_date - timedelta(days=7)
            last_month = current_date - timedelta(days=30)
            
            metrics = {
                'system_health': {
                    'active_projects_percentage': self._calculate_active_project_percentage(),
                    'task_completion_rate': self._calculate_task_completion_rate(),
                    'team_utilization': self._calculate_team_utilization(),
                },
                'recent_activity': {
                    'new_projects_week': Project.objects.filter(created_at__gte=last_week).count(),
                    'completed_tasks_week': Task.objects.filter(
                        status='DONE', 
                        updated_at__gte=last_week
                    ).count(),
                    'new_recommendations_week': AIRecommendation.objects.filter(
                        created_at__gte=last_week
                    ).count(),
                },
                'trends': {
                    'project_growth': self._calculate_project_growth_trend(),
                    'productivity_trend': self._calculate_productivity_trend(),
                }
            }
            
            return metrics
        except Exception as e:
            return {'error': str(e)}
    
    def get_comprehensive_context(self):
        """Get all available sanitized data for AI"""
        context = {
            'user_info': {
                'role': self.role,
                'name': self.user.get_full_name() if self.user and hasattr(self.user, 'get_full_name') else 'Anonymous',
                'access_level': 'full' if self.role in ['HR', 'MANAGER'] else 'limited'
            },
            'projects': self.get_projects_data(),
            'tasks': self.get_tasks_data(),
            'team': self.get_team_data(),
            'ai_recommendations': self.get_ai_recommendations_summary(),
            'system_metrics': self.get_system_metrics(),
            'timestamp': timezone.now().isoformat(),
            'query_scope': self._get_query_scope()
        }
        return context
    
    def sanitize_ai_response(self, response_text):
        """Remove sensitive information from AI responses"""
        if not response_text:
            return "I couldn't generate a response. Please try rephrasing your question."
        
        # Patterns to sanitize
        sensitive_patterns = [
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]'),
            (r'\b\d{10,15}\b', '[ID_REDACTED]'),
            (r'\bpassword\b', '[REDACTED]'),
            (r'\bapi[_\s]?key\b', '[REDACTED]'),
            (r'\bsecret\b', '[REDACTED]'),
            (r'\btoken\b', '[REDACTED]'),
        ]
        
        sanitized = response_text
        for pattern, replacement in sensitive_patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def _get_project_team_size(self, project):
        """Helper to get project team size"""
        try:
            if hasattr(project, 'tasks'):
                return project.tasks.values('assigned_to').distinct().count()
            return 0
        except:
            return 0
    
    def _get_overdue_tasks_count(self, tasks_queryset):
        """Get count of overdue tasks"""
        try:
            today = timezone.now().date()
            return tasks_queryset.filter(
                due_date__lt=today,
                status__in=['TODO', 'IN_PROGRESS']
            ).count()
        except:
            return 0
    
    def _calculate_active_project_percentage(self):
        """Calculate percentage of active projects"""
        try:
            total = Project.objects.count()
            active = Project.objects.filter(status__in=['Ongoing', 'Active']).count()
            return round((active / total * 100), 1) if total > 0 else 0
        except:
            return 0
    
    def _calculate_task_completion_rate(self):
        """Calculate overall task completion rate"""
        try:
            total = Task.objects.count()
            completed = Task.objects.filter(status='DONE').count()
            return round((completed / total * 100), 1) if total > 0 else 0
        except:
            return 0
    
    def _calculate_team_utilization(self):
        """Calculate team utilization percentage"""
        try:
            # This is a simplified calculation - you can make it more sophisticated
            active_users = User.objects.filter(
                is_active=True,
                tasks__isnull=False
            ).distinct().count()
            total_users = User.objects.filter(is_active=True).count()
            return round((active_users / total_users * 100), 1) if total_users > 0 else 0
        except:
            return 0
    
    def _calculate_project_growth_trend(self):
        """Calculate project growth trend"""
        try:
            last_month = timezone.now() - timedelta(days=30)
            recent_projects = Project.objects.filter(created_at__gte=last_month).count()
            return 'growing' if recent_projects > 0 else 'stable'
        except:
            return 'stable'
    
    def _calculate_productivity_trend(self):
        """Calculate productivity trend"""
        try:
            last_week = timezone.now() - timedelta(days=7)
            completed_recently = Task.objects.filter(
                status='DONE',
                updated_at__gte=last_week
            ).count()
            return 'high' if completed_recently > 5 else 'moderate'
        except:
            return 'moderate'
    
    def _get_query_scope(self):
        """Get the scope of data the user can query"""
        if self.role == 'HR':
            return 'all_data'
        elif self.role == 'MANAGER':
            return 'managed_projects_and_team'
        else:
            return 'assigned_tasks_only'

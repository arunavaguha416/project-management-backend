# ai_insights/views/ai_views.py

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from django.utils import timezone
import datetime
import random

from ..models.ai_models import AIRecommendation, ProjectHealthMetric, AIInsight, AIAnalyticsData
from ai_insights.serializers.serializers import *
from projects.models.project_model import Project

# API to generate and add AI recommendations
class AIRecommendationAdd(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            # You can either accept manual data or generate AI recommendations
            if request.data.get('generate_ai', False):
                # Generate mock AI recommendations
                mock_recommendations = self._generate_mock_recommendations(request.user)
                
                created_recommendations = []
                for rec_data in mock_recommendations:
                    rec_data['created_by'] = request.user.id
                    serializer = AIRecommendationSerializer(data=rec_data)
                    if serializer.is_valid():
                        recommendation = serializer.save()
                        created_recommendations.append(serializer.data)
                
                return Response({
                    'status': True,
                    'message': f'{len(created_recommendations)} AI recommendations generated successfully',
                    'records': created_recommendations
                }, status=status.HTTP_200_OK)
            else:
                # Manual recommendation creation
                data = request.data.copy()
                data['created_by'] = request.user.id
                
                serializer = AIRecommendationSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'status': True,
                        'message': 'AI recommendation added successfully',
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
                'message': 'An error occurred while adding AI recommendation',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def _generate_mock_recommendations(self, user):
        """Generate mock AI recommendations"""
        recommendations = [
            {
                'title': 'Reassign John Smith to Project Alpha',
                'description': 'Based on skill analysis, John\'s React expertise would be 40% more effective on Project Alpha',
                'recommendation_type': 'reallocation',
                'impact': 'high',
                'confidence': random.randint(80, 95),
                'severity': 'warning'
            },
            {
                'title': 'Consider hiring a Senior DevOps Engineer',
                'description': 'Current workload analysis shows 15% capacity shortage in infrastructure team',
                'recommendation_type': 'hiring',
                'impact': 'medium',
                'confidence': random.randint(70, 85),
                'severity': 'info'
            },
            {
                'title': 'Optimize sprint planning process',
                'description': 'AI analysis suggests 20% improvement in velocity with adjusted sprint planning',
                'recommendation_type': 'optimization',
                'impact': 'medium',
                'confidence': random.randint(75, 90),
                'severity': 'info'
            },
            {
                'title': 'Risk mitigation for Project Beta',
                'description': 'Timeline analysis indicates potential 2-week delay risk in current trajectory',
                'recommendation_type': 'risk_mitigation',
                'impact': 'high',
                'confidence': random.randint(85, 98),
                'severity': 'critical'
            }
        ]
        return recommendations


# API to list AI recommendations with search and pagination
class AIRecommendationList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)
            search_title = search_data.get('title', '')
            recommendation_type = search_data.get('recommendation_type', '')
            impact = search_data.get('impact', '')
            is_applied = search_data.get('is_applied')
            project_id = search_data.get('project_id')

            query = Q()

            if search_title:
                query &= Q(title__icontains=search_title)
            if recommendation_type:
                query &= Q(recommendation_type=recommendation_type)
            if impact:
                query &= Q(impact=impact)
            if is_applied is not None:
                query &= Q(is_applied=is_applied)
            if project_id:
                query &= Q(project_id=project_id)

            # Filter by user role permissions
            if not request.user.is_staff:
                query &= Q(created_by=request.user)

            recommendations = AIRecommendation.objects.filter(query).order_by('-created_at')

            if recommendations.exists():
                if page is not None:
                    paginator = Paginator(recommendations, page_size)
                    paginated_recommendations = paginator.get_page(page)
                    serializer = AIRecommendationListSerializer(paginated_recommendations, many=True)
                    
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = AIRecommendationListSerializer(recommendations, many=True)
                    return Response({
                        'status': True,
                        'count': recommendations.count(),
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'AI recommendations not found',
                    'records': []
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# API to get AI recommendation details
class AIRecommendationDetails(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            recommendation_id = request.data.get('id')
            if recommendation_id:
                recommendation = AIRecommendation.objects.filter(id=recommendation_id).first()
                
                if recommendation:
                    # Check permissions
                    if not request.user.is_staff and recommendation.created_by != request.user:
                        return Response({
                            'status': False,
                            'message': 'Permission denied',
                        }, status=status.HTTP_403_FORBIDDEN)
                    
                    serializer = AIRecommendationSerializer(recommendation)
                    return Response({
                        'status': True,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': False,
                        'message': 'AI recommendation not found',
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({
                    'status': False,
                    'message': 'Please provide recommendation ID'
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching recommendation details',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# API to apply an AI recommendation
class AIRecommendationApply(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            recommendation_id = request.data.get('id')
            recommendation = AIRecommendation.objects.filter(id=recommendation_id).first()

            if recommendation:
                if not recommendation.deleted_at:
                    if not recommendation.is_applied:
                        recommendation.is_applied = True
                        recommendation.applied_by = request.user
                        recommendation.applied_at = timezone.now()
                        recommendation.save()

                        return Response({
                            'status': True,
                            'message': 'AI recommendation applied successfully'
                        }, status=status.HTTP_200_OK)
                    else:
                        return Response({
                            'status': False,
                            'message': 'AI recommendation is already applied'
                        }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({
                        'status': False,
                        'message': 'Cannot apply a deleted recommendation'
                    }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'status': False,
                'message': 'AI recommendation not found'
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while applying the recommendation',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# API to update an AI recommendation
class AIRecommendationUpdate(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        try:
            recommendation_id = request.data.get('id')
            recommendation = AIRecommendation.objects.filter(id=recommendation_id).first()

            if recommendation:
                # Check permissions
                if not request.user.is_staff and recommendation.created_by != request.user:
                    return Response({
                        'status': False,
                        'message': 'Permission denied',
                    }, status=status.HTTP_403_FORBIDDEN)

                if not recommendation.deleted_at:
                    serializer = AIRecommendationSerializer(recommendation, data=request.data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return Response({
                            'status': True,
                            'message': 'AI recommendation updated successfully'
                        }, status=status.HTTP_200_OK)
                    
                    return Response({
                        'status': False,
                        'message': 'Invalid data',
                        'errors': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({
                        'status': False,
                        'message': 'Cannot update a deleted recommendation'
                    }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'status': False,
                'message': 'AI recommendation not found'
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while updating the recommendation',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# API to soft delete an AI recommendation
class AIRecommendationDelete(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, recommendation_id):
        try:
            recommendation = AIRecommendation.objects.filter(id=recommendation_id).first()

            if recommendation:
                # Check permissions
                if not request.user.is_staff and recommendation.created_by != request.user:
                    return Response({
                        'status': False,
                        'message': 'Permission denied',
                    }, status=status.HTTP_403_FORBIDDEN)

                if not recommendation.deleted_at:
                    recommendation.soft_delete()
                    return Response({
                        'status': True,
                        'message': 'AI recommendation deleted successfully'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': False,
                        'message': 'AI recommendation is already deleted'
                    }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'status': False,
                'message': 'AI recommendation not found'
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# API to get or create project health metrics
class ProjectHealthMetricView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, project_id):
        try:
            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response({
                    'status': False,
                    'message': 'Project not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Get or create health metric
            health_metric, created = ProjectHealthMetric.objects.get_or_create(
                project=project,
                defaults={
                    'overall_score': random.randint(60, 95),
                    'timeline_risk': random.randint(20, 80),
                    'resource_risk': random.randint(20, 80),
                    'quality_risk': random.randint(20, 80),
                    'budget_risk': random.randint(20, 80),
                    'team_efficiency': random.randint(70, 95),
                    'risk_level': random.choice(['low', 'medium', 'high']),
                    'last_analyzed_by': request.user
                }
            )

            if not created:
                # Update with fresh data
                health_metric.overall_score = random.randint(60, 95)
                health_metric.timeline_risk = random.randint(20, 80)
                health_metric.resource_risk = random.randint(20, 80)
                health_metric.quality_risk = random.randint(20, 80)
                health_metric.budget_risk = random.randint(20, 80)
                health_metric.team_efficiency = random.randint(70, 95)
                health_metric.last_analyzed_by = request.user
                health_metric.save()

            serializer = ProjectHealthMetricSerializer(health_metric)
            
            # Add predictions data
            predictions = [
                {
                    'id': 1,
                    'type': 'timeline',
                    'message': f'Project health analyzed for {project.name}',
                    'confidence': random.randint(70, 95),
                    'severity': 'info'
                },
                {
                    'id': 2,
                    'type': 'resource',
                    'message': f'Resource optimization suggested for improved efficiency',
                    'confidence': random.randint(80, 95),
                    'severity': 'warning' if health_metric.resource_risk > 60 else 'info'
                }
            ]

            response_data = serializer.data
            response_data['predictions'] = predictions

            return Response({
                'status': True,
                'records': response_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# API to get AI dashboard analytics
class AIAnalyticsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            # Get AI metrics for the user/organization
            total_recommendations = AIRecommendation.objects.count()
            applied_recommendations = AIRecommendation.objects.filter(is_applied=True).count()
            
            # Calculate average health scores
            avg_health = ProjectHealthMetric.objects.aggregate(
                avg_overall=Avg('overall_score'),
                avg_efficiency=Avg('team_efficiency')
            )

            analytics_data = {
                'total_recommendations': total_recommendations,
                'applied_recommendations': applied_recommendations,
                'avg_project_health': int(avg_health['avg_overall'] or 75),
                'avg_team_efficiency': int(avg_health['avg_efficiency'] or 80),
                'cost_savings': random.randint(15000, 50000),
                'efficiency_boost': random.randint(25, 45),
                'automation_rate': random.randint(60, 90),
                'active_insights': AIInsight.objects.filter(is_active=True).count()
            }

            return Response({
                'status': True,
                'records': analytics_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# API to get AI insights for managers
class AIManagerInsightsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            # Mock manager insights data
            manager_insights = {
                'resourceOptimization': random.randint(8, 15),
                'projectRiskLevel': random.choice(['low', 'medium', 'high']),
                'teamEfficiency': random.randint(75, 95),
                'aiRecommendations': AIRecommendation.objects.filter(
                    created_by=request.user,
                    is_applied=False
                ).count(),
                'cost_savings': random.randint(20000, 60000),
                'time_savings': f"{random.randint(15, 40)}%",
                'team_satisfaction': f"{random.randint(80, 95)}%"
            }

            return Response({
                'status': True,
                'data': manager_insights
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# API to get AI insights for HR
class AIHRInsightsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            # Mock HR insights data
            hr_insights = {
                'hrEfficiency': random.randint(85, 98),
                'automatedTasks': random.randint(12, 25),
                'predictiveInsights': random.randint(6, 15),
                'riskAlerts': random.randint(2, 8),
                'employee_satisfaction': f"{random.randint(85, 95)}%",
                'recruitment_optimization': f"{random.randint(30, 50)}%",
                'retention_prediction': f"{random.randint(90, 98)}%"
            }

            return Response({
                'status': True,
                'data': hr_insights
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# API to get AI insights for employees
class AIEmployeeInsightsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            # Mock employee insights data
            employee_insights = {
                'productivity': random.randint(80, 95),
                'taskOptimization': random.randint(3, 8),
                'learningPaths': random.randint(2, 6),
                'workloadBalance': random.choice(['good', 'moderate', 'high']),
                'skill_improvement': f"{random.randint(15, 30)}%",
                'efficiency_score': f"{random.randint(85, 95)}%",
                'goal_completion': f"{random.randint(80, 95)}%"
            }

            return Response({
                'status': True,
                'data': employee_insights
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

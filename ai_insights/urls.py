# ai_insights/urls.py

from django.urls import path
from .views.ai_views import *

# URL patterns for AI-related API endpoints

urlpatterns = [
    # AI Recommendations
    path('recommendations/add/', AIRecommendationAdd.as_view(), name='ai-recommendation-add'),
    path('recommendations/list/', AIRecommendationList.as_view(), name='ai-recommendation-list'),
    path('recommendations/details/', AIRecommendationDetails.as_view(), name='ai-recommendation-details'),
    path('recommendations/update/', AIRecommendationUpdate.as_view(), name='ai-recommendation-update'),
    path('recommendations/delete/<uuid:recommendation_id>/', AIRecommendationDelete.as_view(), name='ai-recommendation-delete'),
    path('recommendations/apply/', AIRecommendationApply.as_view(), name='ai-recommendation-apply'),
    
    # Project Health Metrics
    path('health/<uuid:project_id>/', ProjectHealthMetricView.as_view(), name='project-health-metric'),
    
    # AI Analytics
    path('analytics/', AIAnalyticsView.as_view(), name='ai-analytics'),
    
    # Role-specific Insights
    path('insights/manager/', AIManagerInsightsView.as_view(), name='ai-manager-insights'),
    path('insights/hr/', AIHRInsightsView.as_view(), name='ai-hr-insights'),
    path('insights/employee/', AIEmployeeInsightsView.as_view(), name='ai-employee-insights'),
]

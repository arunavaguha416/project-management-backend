# ai_insights/urls.py

from django.urls import path
from .views.ai_views import *

# URL patterns for AI-related API endpoints
urlpatterns = [
    # AI Chat Assistant (Main AI endpoint for dashboard assistants)
    path('chat/', AIChatView.as_view(), name='ai-chat'),
    
    # AI Status and Testing
    path('test-google-ai/', TestGoogleAI.as_view(), name='test-google-ai'),
    
    # Role-specific AI Insights
    path('manager-insights/', AIManagerInsightsView.as_view(), name='ai-manager-insights'),
    path('hr-insights/', AIHRInsightsView.as_view(), name='ai-hr-insights'),
    path('employee-insights/', AIEmployeeInsightsView.as_view(), name='ai-employee-insights'),
    
    # AI Recommendations CRUD
    path('recommendations/add/', AIRecommendationAdd.as_view(), name='ai-recommendation-add'),
    path('recommendations/list/', AIRecommendationList.as_view(), name='ai-recommendation-list'),
    path('recommendations/details/', AIRecommendationDetails.as_view(), name='ai-recommendation-details'),
    path('recommendations/update/', AIRecommendationUpdate.as_view(), name='ai-recommendation-update'),
    path('recommendations/delete/<int:recommendation_id>/', AIRecommendationDelete.as_view(), name='ai-recommendation-delete'),
    path('recommendations/apply/', AIRecommendationApply.as_view(), name='ai-recommendation-apply'),
    
    # Project Health Metrics
    path('health/<int:project_id>/', ProjectHealthMetricView.as_view(), name='project-health-metric'),
    
    # AI Analytics Dashboard
    path('analytics/', AIAnalyticsView.as_view(), name='ai-analytics'),
]

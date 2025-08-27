# ai_insights/serializers/ai_serializers.py

from rest_framework import serializers
from ..models.ai_models import AIRecommendation, ProjectHealthMetric, AIInsight, AIAnalyticsData
from authentication.models.user import User
from projects.models.project_model import Project

# Serializer for the AIRecommendation model
class AIRecommendationSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    applied_by_name = serializers.CharField(source='applied_by.get_full_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = AIRecommendation
        fields = [
            'id', 'title', 'description', 'recommendation_type', 
            'impact', 'severity', 'confidence', 'project', 'project_name',
            'created_by', 'created_by_name', 'applied_by', 'applied_by_name',
            'is_applied', 'applied_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'applied_at']


# Serializer for the ProjectHealthMetric model
class ProjectHealthMetricSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_manager = serializers.CharField(source='project.manager.get_full_name', read_only=True)
    analyzed_by_name = serializers.CharField(source='last_analyzed_by.get_full_name', read_only=True)
    
    class Meta:
        model = ProjectHealthMetric
        fields = [
            'id', 'project', 'project_name', 'project_manager',
            'overall_score', 'timeline_risk', 'resource_risk', 
            'quality_risk', 'budget_risk', 'team_efficiency',
            'risk_level', 'last_analyzed_by', 'analyzed_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# Serializer for the AIInsight model
class AIInsightSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.CharField(source='generated_by.get_full_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = AIInsight
        fields = [
            'id', 'title', 'description', 'insight_type', 'data',
            'project', 'project_name', 'generated_by', 'generated_by_name',
            'is_active', 'confidence_score', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# Serializer for the AIAnalyticsData model
class AIAnalyticsDataSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = AIAnalyticsData
        fields = [
            'id', 'analytics_type', 'data', 'project', 'project_name',
            'user', 'user_name', 'date_range_start', 'date_range_end',
            'is_processed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# Simplified serializer for listing recommendations
class AIRecommendationListSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = AIRecommendation
        fields = [
            'id', 'title', 'recommendation_type', 'impact', 
            'confidence', 'project_name', 'created_by_name',
            'is_applied', 'created_at'
        ]


# Simplified serializer for project health overview
class ProjectHealthOverviewSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = ProjectHealthMetric
        fields = [
            'id', 'project_name', 'overall_score', 'risk_level', 'updated_at'
        ]

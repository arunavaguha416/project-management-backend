# ai_insights/models/ai_models.py

from django.db import models
from project_management.softDeleteModel import SoftDeletionModel
import uuid
from authentication.models.user import User
from projects.models.project_model import Project

# Define the AIRecommendation model to represent AI-generated suggestions
class AIRecommendation(SoftDeletionModel):
    RECOMMENDATION_TYPES = [
        ('reallocation', 'Resource Reallocation'),
        ('hiring', 'Hiring Suggestion'),
        ('optimization', 'Process Optimization'),
        ('risk_mitigation', 'Risk Mitigation'),
        ('cost_reduction', 'Cost Reduction'),
    ]
    
    IMPACT_LEVELS = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    SEVERITY_LEVELS = [
        ('critical', 'Critical'),
        ('warning', 'Warning'),
        ('info', 'Info'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    recommendation_type = models.CharField(
        max_length=20, 
        choices=RECOMMENDATION_TYPES,
        default='optimization'
    )
    impact = models.CharField(
        max_length=10, 
        choices=IMPACT_LEVELS,
        default='medium'
    )
    severity = models.CharField(
        max_length=10, 
        choices=SEVERITY_LEVELS,
        default='info'
    )
    confidence = models.IntegerField(default=50)  # 0-100
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='ai_recommendations'
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='created_recommendations'
    )
    applied_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applied_recommendations'
    )
    is_applied = models.BooleanField(default=False)
    applied_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "AI Recommendation"
        verbose_name_plural = "AI Recommendations"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.recommendation_type}"


# Define the ProjectHealthMetric model to track project health scores
class ProjectHealthMetric(SoftDeletionModel):
    RISK_LEVELS = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    project = models.OneToOneField(
        Project, 
        on_delete=models.CASCADE,
        related_name='health_metric'
    )
    overall_score = models.IntegerField(default=50)  # 0-100
    timeline_risk = models.IntegerField(default=50)  # 0-100
    resource_risk = models.IntegerField(default=50)  # 0-100
    quality_risk = models.IntegerField(default=50)  # 0-100
    budget_risk = models.IntegerField(default=50)  # 0-100
    team_efficiency = models.IntegerField(default=50)  # 0-100
    risk_level = models.CharField(
        max_length=10,
        choices=RISK_LEVELS,
        default='medium'
    )
    last_analyzed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analyzed_health_metrics'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Project Health Metric"
        verbose_name_plural = "Project Health Metrics"
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.project.name} - Health Score: {self.overall_score}%"


# Define the AIInsight model to store AI-generated insights
class AIInsight(SoftDeletionModel):
    INSIGHT_TYPES = [
        ('productivity', 'Productivity Analysis'),
        ('resource_optimization', 'Resource Optimization'),
        ('timeline_prediction', 'Timeline Prediction'),
        ('cost_analysis', 'Cost Analysis'),
        ('team_performance', 'Team Performance'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    insight_type = models.CharField(
        max_length=25,
        choices=INSIGHT_TYPES,
        default='productivity'
    )
    data = models.JSONField(default=dict, blank=True)  # Store insight data
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='ai_insights'
    )
    generated_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='generated_insights'
    )
    is_active = models.BooleanField(default=True)
    confidence_score = models.IntegerField(default=50)  # 0-100
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "AI Insight"
        verbose_name_plural = "AI Insights"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.insight_type}"


# Define the AIAnalyticsData model to store analytics information
class AIAnalyticsData(SoftDeletionModel):
    ANALYTICS_TYPES = [
        ('team_efficiency', 'Team Efficiency'),
        ('project_velocity', 'Project Velocity'),
        ('resource_utilization', 'Resource Utilization'),
        ('cost_tracking', 'Cost Tracking'),
        ('timeline_accuracy', 'Timeline Accuracy'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    analytics_type = models.CharField(
        max_length=25,
        choices=ANALYTICS_TYPES
    )
    data = models.JSONField(default=dict)  # Store analytics data
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='analytics_data'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='analytics_data'
    )
    date_range_start = models.DateTimeField()
    date_range_end = models.DateTimeField()
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "AI Analytics Data"
        verbose_name_plural = "AI Analytics Data"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.analytics_type} - {self.created_at.date()}"

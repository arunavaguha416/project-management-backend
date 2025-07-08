# company/serializers.py
from rest_framework import serializers
from company.models.company_model import Company

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']

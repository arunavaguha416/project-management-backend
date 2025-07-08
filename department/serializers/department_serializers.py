# department/serializers.py
from rest_framework import serializers
from ..models.department_model import Department
from authentication.models.user import User

# Serializer for the Department model
class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
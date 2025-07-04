# department/serializers.py
from rest_framework import serializers
from ..models.depertment_model import Department
from authentication.models.user import User

# Serializer for the Department model
class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'manager', 'published_at', 'created_at', 'updated_at']
from rest_framework import serializers
from .models import Element


class ProblemListSerializer(serializers.ModelSerializer):
    problem_name = serializers.CharField(
        source='pname',
        read_only=True
    )

    class Meta:
        model = Element
        fields = [
            'id',
            'problem_name',
            'rating',
            'category',
            'author',
        ]
class ProblemDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Element
        fields = [
            'id',
            'pname',
            'description',
            'rating',
            'category',
            'contest',
        ]
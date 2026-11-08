from rest_framework import serializers
from .models import Submission, Standings
from django.utils import timezone


class SubmissionListSerializer(serializers.ModelSerializer):
    handle = serializers.CharField(
        source='student.handle',
        read_only=True
    )

    problem_name = serializers.CharField(
        source='element.pname',
        read_only=True
    )

    contest_name = serializers.CharField(
        source='contest.cname',
        read_only=True,
        allow_null=True
    )

    code = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            'code',
            'handle',
            'problem_name',
            'contest_name',
            'language',
            'verdict',
            'submitted_at',
            'execution_time',
            'memory',
        ]

    def get_code(self, obj):
        # Hide source code while contest is running
        if obj.contest and timezone.now() < obj.contest.end_datetime:
            return None

        return obj.code
class StandingsSerializer(serializers.ModelSerializer):

    handle = serializers.CharField(
        source='student.handle',
        read_only=True
    )

    class Meta:
        model = Standings
        fields = [
            'handle',
            'rank',
            'penalty',
            'solved',
            'rating'
        ]



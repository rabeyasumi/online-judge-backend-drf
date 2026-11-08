
from rest_framework import serializers
from django.utils import timezone

from .models import Contest, GlobalStanding, RatingChange



class ContestSerializer(serializers.ModelSerializer):

    status = serializers.SerializerMethodField()

    class Meta:
        model = Contest
        fields = [
            'id',
            'cname',
            'tag',
            'status',
            'start_datetime',
            'end_datetime',
        ]

    def get_status(self, obj):

        now = timezone.now()

        if obj.start_datetime > now:
            return 'upcoming'

        elif obj.end_datetime > now:
            return 'running'

        return 'past'


class GlobalStandingSerializer(serializers.ModelSerializer):
    handle = serializers.CharField(source='student.handle', read_only=True)

    class Meta:
        model = GlobalStanding
        fields = ['handle', 'rank', 'rating', 'rated_contests']


class RatingChangeSerializer(serializers.ModelSerializer):
    handle = serializers.CharField(source='student.handle', read_only=True)
    contest_name = serializers.CharField(source='contest.cname', read_only=True)
    rating_change = serializers.SerializerMethodField()

    class Meta:
        model = RatingChange
        fields = [
            'id',
            'handle',
            'contest',
            'contest_name',
            'old_rating',
            'new_rating',
            'rating_change',
            'created_at',
        ]

    def get_rating_change(self, obj):
        return round(obj.rating_change, 2)



from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.filters import SearchFilter
from rest_framework.exceptions import ValidationError


from rest_framework.pagination import PageNumberPagination

from django.utils import timezone

from .models import Contest, GlobalStanding, RatingChange
from .serializers import (
    ContestSerializer,
    GlobalStandingSerializer,
    RatingChangeSerializer,
)

class ContestPagination(PageNumberPagination):
    page_size = 8


class ContestListView(generics.ListAPIView):

    queryset = Contest.objects.all()
    serializer_class = ContestSerializer
    permission_classes = [AllowAny]
    pagination_class = ContestPagination

    filter_backends = [SearchFilter]
    search_fields = ['cname', 'tag']

    def get_queryset(self):

        queryset = super().get_queryset()

        status = self.request.query_params.get('status')

        if status:

            status = status.lower()
            now = timezone.now()

            if status == 'upcoming':
                queryset = queryset.filter(
                    start_datetime__gt=now
                )

            elif status == 'running':
                queryset = queryset.filter(
                    start_datetime__lte=now,
                    end_datetime__gt=now
                )

            elif status == 'past':
                queryset = queryset.filter(
                    end_datetime__lte=now
                )

            else:
                raise ValidationError({
                    'status': 'Invalid status. Choose upcoming, running or past.'
                })

        return queryset
    def paginate_queryset(self, queryset):
        status = self.request.query_params.get('status', '').lower()

        if status == 'past':
            return super().paginate_queryset(queryset)

        return None
    
class ContestDetailView(generics.RetrieveAPIView):

    queryset = Contest.objects.all()
    serializer_class = ContestSerializer
    permission_classes = [AllowAny]

class GlobalStandingListView(generics.ListAPIView):
    """GET /api/contests/global-standings/"""

    serializer_class = GlobalStandingSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return GlobalStanding.objects.select_related('student').order_by(
            'rank', 'student__handle'
        )


class RatingChangeListView(generics.ListAPIView):
    """GET /api/contests/rating-changes/?contest=<id>&handle=<handle>"""

    serializer_class = RatingChangeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = RatingChange.objects.select_related('student', 'contest')

        contest = self.request.query_params.get('contest')
        handle = self.request.query_params.get('handle')
        if contest and contest.isdigit():
            qs = qs.filter(contest_id=int(contest))
        if handle:
            qs = qs.filter(student__handle__iexact=handle)

        return qs.order_by('-created_at', '-id')


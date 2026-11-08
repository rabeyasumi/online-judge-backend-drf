from django.contrib import admin, messages
from django.utils import timezone
from submissions.models import Standings 
from .models import Contest, GlobalStanding, RatingChange
from .services.global_rating import process_rated_contest


@admin.action(description="🚀 Process Global Ratings for selected contests")
def process_ratings_action(modeladmin, request, queryset):
    # Oldest first, so each contest builds on the previous contest's ratings.
    for contest in queryset.order_by('end_datetime', 'id'):

        if not Standings.objects.filter(contest=contest).exists():
            modeladmin.message_user(
                request,
                f"'{contest.cname}': no standings found, nothing to rate.",
                messages.WARNING
            )
            continue

        try:
            result = process_rated_contest(contest)

        except ValueError as e:
            # not rated / already processed / not ended / no participants
            modeladmin.message_user(
                request, f"'{contest.cname}': {e}", messages.WARNING
            )

        except Exception as e:
            modeladmin.message_user(
                request, f"Failed to process '{contest.cname}': {e}",
                messages.ERROR
            )

        else:
            modeladmin.message_user(
                request,
                f"Updated global ratings for '{result['contest']}' "
                f"({len(result['participants'])} participants).",
                messages.SUCCESS
            )

@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):

    list_display = [
        'id',
        'cname',
        'tag',
        'get_status',
        'start_datetime',
        'end_datetime',
        'is_rated',
        'rating_processed',
    ]

    list_filter = [
        'tag',
        'is_rated',
        'rating_processed',
    ]

    search_fields = [
        'cname',
        'tag',
    ]

    ordering = ['-start_datetime']

    actions = [process_ratings_action]

    @admin.display(description='Status')
    def get_status(self, obj):

        now = timezone.now()

        if obj.start_datetime > now:
            return 'Upcoming'

        elif obj.end_datetime > now:
            return 'Running'

        return 'Past'


@admin.register(GlobalStanding)
class GlobalStandingAdmin(admin.ModelAdmin):
    list_display = ['student', 'rank', 'rating', 'rated_contests']
    ordering = ['rank']
    search_fields = ['student__handle']


@admin.register(RatingChange)
class RatingChangeAdmin(admin.ModelAdmin):
    list_display = ['student', 'contest', 'old_rating', 'new_rating', 'delta', 'created_at']
    list_filter = ['contest']
    search_fields = ['student__handle']

    @admin.display(description='Change')
    def delta(self, obj):
        return obj.rating_change

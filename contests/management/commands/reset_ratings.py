from django.core.management.base import BaseCommand

from contests.models import Contest, GlobalStanding, RatingChange
from profiles.models import ProfileSubmissionStatistics


class Command(BaseCommand):
    help = ('Delete all global ratings / rating history and mark every contest '
            'as not processed, so ratings can be recalculated from scratch.')

    def add_arguments(self, parser):
        parser.add_argument('--yes', action='store_true', help='Confirm the reset.')

    def handle(self, *args, **options):
        if not options['yes']:
            self.stdout.write(self.style.WARNING(
                'This deletes GlobalStanding and RatingChange rows. '
                'Re-run with --yes to confirm.'
            ))
            return

        RatingChange.objects.all().delete()
        GlobalStanding.objects.all().delete()
        ProfileSubmissionStatistics.objects.update(rating=0.0, max_rating=0.0)
        Contest.objects.update(rating_processed=False)
        self.stdout.write(self.style.SUCCESS('Ratings reset.'))

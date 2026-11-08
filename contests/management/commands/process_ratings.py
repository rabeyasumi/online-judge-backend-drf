from django.core.management.base import BaseCommand

from contests.services.global_rating import process_pending_rated_contests


class Command(BaseCommand):
    help = 'Process every ended, rated, not-yet-processed contest (oldest first).'

    def handle(self, *args, **options):
        results = process_pending_rated_contests()

        if not results:
            self.stdout.write(self.style.WARNING('No pending rated contests found.'))
            return

        for result in results:
            if not result['processed']:
                self.stdout.write(self.style.ERROR(
                    f"Failed: {result['contest']} - {result['error']}"
                ))
                continue

            self.stdout.write(self.style.SUCCESS(f"Processed: {result['contest']}"))
            for p in result['participants']:
                self.stdout.write(
                    f"  #{p['rank']} {p['handle']}: {p['old_rating']:.2f} -> "
                    f"{p['new_rating']:.2f} ({p['rating_change']:+.2f})"
                )



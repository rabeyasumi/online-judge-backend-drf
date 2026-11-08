from django.db import transaction
from django.utils import timezone

from contests.models import Contest, GlobalStanding, RatingChange
from submissions.models import Standings          # contest score + rank per student
from profiles.models import ProfileSubmissionStatistics

from .rating_formula import calculate_new_rating


def get_pending_rated_contests():
    return Contest.objects.filter(
        is_rated=True,
        rating_processed=False,
        end_datetime__lte=timezone.now()
    ).order_by('end_datetime', 'id')


def recalculate_global_ranks():
    standings = GlobalStanding.objects.select_related('student').order_by(
        '-rating', 'student__handle'
    )

    current, prev = 0, None
    for index, g in enumerate(standings):
        rating = round(float(g.rating), 2)
        if prev is None or rating != prev:
            current = index + 1
        if g.rank != current:
            g.rank = current
            g.save(update_fields=['rank'])
        prev = rating


@transaction.atomic
def process_rated_contest(contest):
    contest = Contest.objects.select_for_update().get(pk=contest.pk)

    if not contest.is_rated:
        raise ValueError("This contest is not rated.")
    if contest.rating_processed:
        raise ValueError("This contest is already processed.")
    if contest.end_datetime > timezone.now():
        raise ValueError("This contest has not ended yet.")

    standings = list(
        Standings.objects.filter(contest=contest)
        .select_related('student')
        .order_by('rank', 'student_id')
    )
    if not standings:
        raise ValueError("No participants found for this contest.")

    results = []
    for s in standings:
        standing, _ = GlobalStanding.objects.get_or_create(
            student_id=s.student_id,
            defaults={'rating': 0.0, 'rated_contests': 0, 'rank': 0},
        )

        old_rating = float(standing.rating)
        contest_rating = float(s.rating)           # score from Standings
        new_rating = calculate_new_rating(
            old_rating, contest_rating, standing.rated_contests
        )

        standing.rating = new_rating
        standing.rated_contests += 1
        standing.save(update_fields=['rating', 'rated_contests'])

        RatingChange.objects.update_or_create(
            student_id=s.student_id,
            contest=contest,
            defaults={'old_rating': old_rating, 'new_rating': new_rating},
        )

        stats, _ = ProfileSubmissionStatistics.objects.get_or_create(
            student_id=s.student_id
        )
        stats.rating = new_rating
        stats.max_rating = max(stats.max_rating, new_rating)
        stats.save(update_fields=['rating', 'max_rating'])

        results.append({
            'handle': s.student.handle,
            'rank': s.rank,
            'contest_rating': contest_rating,
            'old_rating': old_rating,
            'new_rating': new_rating,
            'rating_change': round(new_rating - old_rating, 2),
        })

    recalculate_global_ranks()

    contest.rating_processed = True
    contest.save(update_fields=['rating_processed'])

    return {'contest': contest.cname, 'participants': results, 'processed': True}


def process_pending_rated_contests():
    results = []
    for contest in list(get_pending_rated_contests()):
        try:
            results.append(process_rated_contest(contest))
        except Exception as error:
            results.append({
                'contest': contest.cname,
                'processed': False,
                'error': str(error),
            })
    return results

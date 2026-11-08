from django.db.models import Q

from submissions.models import Submission
from .rating_calculator import calculate_problem_rating


def calculate_student_problem_points(student, problem, contest):

    submissions = Submission.objects.filter(
        contest=contest,
        student=student,
        element=problem,
        submitted_at__gte=contest.start_datetime,
        submitted_at__lt=contest.end_datetime
    )

    accepted_submission = submissions.filter(
        verdict='Accepted'
    ).order_by('submitted_at', 'id').first()

    if accepted_submission is None:
        return None

    wrong_submission_count = submissions.filter(
        Q(submitted_at__lt=accepted_submission.submitted_at) |
        Q(
            submitted_at=accepted_submission.submitted_at,
            id__lt=accepted_submission.id
        )
    ).exclude(
        verdict='Accepted'
    ).count()

    elapsed_time = (
        accepted_submission.submitted_at - contest.start_datetime
    ).total_seconds() / 60

    problem_points = calculate_problem_rating(
        problem_rating=problem.rating,
        wrong_submission_count=wrong_submission_count,
        elapsed_time=elapsed_time
    )

    return problem_points

def calculate_student_contest_score(student, contest):

    problems = contest.problems.all()

    solved = 0
    total_rating = 0.0

    for problem in problems:
        points = calculate_student_problem_points(
            student=student,
            problem=problem,
            contest=contest
        )

        if points is not None:
            solved += 1
            total_rating += points

    return {
        'solved': solved,
        'rating': round(total_rating, 2)
    }
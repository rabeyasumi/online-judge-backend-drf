
import pytest

from helpers import results_of, submit
from submissions.models import Standings, Submission

pytestmark = pytest.mark.django_db

CASES = (('1 2', '3'),)


@pytest.fixture
def running_contest(make_contest):
    return make_contest(start_min=-10.5, end_min=60)


@pytest.fixture
def contest_problem(make_problem, running_contest):
    return make_problem(contest=running_contest, rating=1000, cases=CASES)


@pytest.fixture
def accept(fake_judge):
    fake_judge.outputs = {'1 2': '3'}
    return fake_judge


def standing_of(student, contest):
    return Standings.objects.get(student=student, contest=contest)


def test_accepted_during_a_contest_creates_a_standing(
    client, student, running_contest, contest_problem, accept
):
    submit(client, contest_problem)

    saved = Submission.objects.get()
    assert saved.contest == running_contest

    row = standing_of(student, running_contest)
    assert row.solved == 1
    assert row.rating == pytest.approx(958, abs=1)
    assert row.penalty == 10
    assert row.rank == 1


def test_wrong_answer_then_accepted_costs_points_and_penalty(
    client, student, running_contest, contest_problem, fake_judge
):
    fake_judge.default_output = 'wrong'
    submit(client, contest_problem)
    fake_judge.outputs = {'1 2': '3'}
    submit(client, contest_problem)

    row = standing_of(student, running_contest)
    assert row.solved == 1
    assert row.rating == pytest.approx(908, abs=1)       # 958 - 50
    assert row.penalty == 30                             # 10 + 20


def test_compile_error_costs_rating_but_not_icpc_penalty(
    client, student, running_contest, contest_problem, fake_judge
):
    """Characterization test: current behaviour, worth knowing about.

    A Compilation Error counts as a failed attempt for the rating score, but
    the ICPC penalty only counts 'Wrong Answer'.
    """
    fake_judge.compile_status = '1'
    submit(client, contest_problem, code='print(')
    fake_judge.compile_status = '0'
    fake_judge.outputs = {'1 2': '3'}
    submit(client, contest_problem)

    row = standing_of(student, running_contest)
    assert row.rating == pytest.approx(908, abs=1)       # 958 - 50
    assert row.penalty == 10                             # no +20 for the compile error


def test_only_wrong_attempts_give_a_zero_row(
    client, student, running_contest, contest_problem, fake_judge
):
    fake_judge.default_output = 'wrong'
    submit(client, contest_problem)

    row = standing_of(student, running_contest)
    assert row.solved == 0
    assert row.rating == 0
    assert row.penalty == 0


def test_judge_error_does_not_touch_standings(
    client, running_contest, contest_problem, fake_judge, judge_down
):
    fake_judge.compile_error = judge_down

    submit(client, contest_problem)

    assert Submission.objects.get().verdict == 'Judge Error'
    assert Standings.objects.count() == 0


def test_practice_problem_has_no_contest_and_no_standing(client, make_problem, accept):
    problem = make_problem(contest=None, cases=CASES)

    submit(client, problem)

    assert Submission.objects.get().contest is None
    assert Standings.objects.count() == 0


def test_submission_after_the_contest_ended_is_not_ranked(
    client, make_contest, make_problem, accept
):
    ended = make_contest(start_min=-180, end_min=-60)
    problem = make_problem(contest=ended, cases=CASES)

    response = submit(client, problem)

    assert response.json()['verdict'] == 'Accepted'
    assert Submission.objects.get().contest == ended     # still recorded against the contest
    assert Standings.objects.count() == 0


def test_submission_before_the_contest_started_is_not_ranked(
    client, make_contest, make_problem, accept
):
    upcoming = make_contest(start_min=60, end_min=180)
    problem = make_problem(contest=upcoming, cases=CASES)

    submit(client, problem)

    assert Standings.objects.count() == 0


def test_ranks_follow_the_score(
    make_student, make_client, running_contest, contest_problem, fake_judge, anon_client
):
    alice, bob = make_student('alice2'), make_student('bob2')

    fake_judge.outputs = {'1 2': '3'}
    submit(make_client(alice), contest_problem)          
    fake_judge.outputs = {}
    fake_judge.default_output = 'wrong'
    submit(make_client(bob), contest_problem)            

    response = anon_client.get(f'/api/contests/{running_contest.id}/standings/')
    assert response.status_code == 200
    rows = results_of(response)
    assert [(r['handle'], r['rank'], r['solved']) for r in rows] == [
        ('alice2', 1, 1),
        ('bob2', 2, 0),
    ]


def test_equal_scores_share_a_rank(
    make_student, make_client, running_contest, contest_problem, fake_judge
):
    first, second = make_student('tie1'), make_student('tie2')
    fake_judge.outputs = {'1 2': '3'}

    submit(make_client(first), contest_problem)
    submit(make_client(second), contest_problem)

    ranks = {
        r.student.handle: r.rank
        for r in Standings.objects.filter(contest=running_contest).select_related('student')
    }
    
    assert sorted(ranks.values()) in ([1, 1], [1, 2])

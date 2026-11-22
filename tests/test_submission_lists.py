
from datetime import timedelta

import pytest
from django.utils import timezone

from helpers import results_of
from submissions.models import Submission

pytestmark = pytest.mark.django_db

MY = '/api/submissions/my/'
ALL = '/api/submissions/all/'


@pytest.fixture
def make_submission(db):
    def _make(student, problem, contest=None, verdict='Accepted', minutes_ago=0, code='print(1)'):
        return Submission.objects.create(
            student=student, element=problem, contest=contest, code=code,
            language='python3', verdict=verdict,
            submitted_at=timezone.now() - timedelta(minutes=minutes_ago),
        )
    return _make


# ------------------------------------------------------------------ my/

def test_my_requires_login(anon_client):
    assert anon_client.get(MY).status_code == 401


def test_my_shows_only_my_submissions(client, student, make_student, make_problem, make_submission):
    problem = make_problem()
    other = make_student('other')
    make_submission(student, problem)
    make_submission(other, problem)

    rows = results_of(client.get(MY))

    assert [r['handle'] for r in rows] == ['alice']


def test_my_is_newest_first(client, student, make_problem, make_submission):
    problem = make_problem()
    make_submission(student, problem, minutes_ago=30, verdict='Wrong Answer')
    make_submission(student, problem, minutes_ago=10, verdict='Accepted')
    make_submission(student, problem, minutes_ago=20, verdict='Compilation Error')

    rows = results_of(client.get(MY))

    assert [r['verdict'] for r in rows] == ['Accepted', 'Compilation Error', 'Wrong Answer']


def test_my_filters_by_problem(client, student, make_problem, make_submission):
    wanted, other = make_problem(), make_problem()
    make_submission(student, wanted)
    make_submission(student, other)

    rows = results_of(client.get(MY, {'problem_id': wanted.id}))

    assert [r['problem_name'] for r in rows] == [wanted.pname]


def test_my_filters_by_contest(client, student, make_contest, make_problem, make_submission):
    contest = make_contest(start_min=-120, end_min=-60)
    in_contest = make_problem(contest=contest)
    practice = make_problem()
    make_submission(student, in_contest, contest=contest)
    make_submission(student, practice)

    rows = results_of(client.get(MY, {'contest': contest.id}))

    assert [r['problem_name'] for r in rows] == [in_contest.pname]


# ------------------------------------------------------------------ all/

def test_all_requires_login(anon_client):
    assert anon_client.get(ALL).status_code == 401


def test_all_shows_everyones_submissions_newest_first(
    client, student, make_student, make_problem, make_submission
):
    problem = make_problem()
    bob = make_student('bob')
    make_submission(student, problem, minutes_ago=20)
    make_submission(bob, problem, minutes_ago=5)

    rows = results_of(client.get(ALL))

    assert [r['handle'] for r in rows] == ['bob', 'alice']


def test_all_filters_by_handle_partially_and_ignoring_case(
    client, student, make_student, make_problem, make_submission
):
    problem = make_problem()
    make_submission(student, problem)                           # alice
    make_submission(make_student('Bobby'), problem)

    rows = results_of(client.get(ALL, {'handle': 'BOB'}))

    assert [r['handle'] for r in rows] == ['Bobby']


def test_all_filters_by_problem_and_contest(
    client, student, make_contest, make_problem, make_submission
):
    contest = make_contest(start_min=-120, end_min=-60)
    a = make_problem(contest=contest)
    b = make_problem()
    make_submission(student, a, contest=contest)
    make_submission(student, b)

    by_problem = results_of(client.get(ALL, {'problem_name': b.pname}))
    by_contest = results_of(client.get(ALL, {'contest_id': contest.id}))

    assert [r['problem_name'] for r in by_problem] == [b.pname]
    assert [r['problem_name'] for r in by_contest] == [a.pname]


def test_all_ignores_filters_that_are_not_numbers(client, student, make_problem, make_submission):
    make_submission(student, make_problem())

    response = client.get(ALL, {'problem_id': 'abc', 'contest_id': 'x'})

    assert response.status_code == 200
    assert len(results_of(response)) == 1


# ------------------------------------------------------------------ source code visibility

def test_code_is_hidden_while_the_contest_is_running(
    client, student, make_contest, make_problem, make_submission
):
    running = make_contest(start_min=-30, end_min=30)
    problem = make_problem(contest=running)
    make_submission(student, problem, contest=running, code='secret()')

    row = results_of(client.get(ALL))[0]

    assert row['code'] is None


def test_code_is_visible_after_the_contest_and_for_practice(
    client, student, make_contest, make_problem, make_submission
):
    ended = make_contest(start_min=-120, end_min=-60)
    in_contest = make_problem(contest=ended)
    practice = make_problem()
    make_submission(student, in_contest, contest=ended, code='after()', minutes_ago=100)
    make_submission(student, practice, code='practice()', minutes_ago=5)

    codes = {r['code'] for r in results_of(client.get(ALL))}

    assert codes == {'after()', 'practice()'}


def test_practice_submission_has_no_contest_name(client, student, make_problem, make_submission):
    make_submission(student, make_problem())

    assert results_of(client.get(MY))[0]['contest_name'] is None

def test_all_filters_by_verdict_and_language(client, student, make_problem, make_submission):
    problem = make_problem()
    make_submission(student, problem, verdict='Accepted')
    make_submission(student, problem, verdict='Wrong Answer')

    rows = results_of(client.get(ALL, {'verdict': 'accepted'}))

    assert [r['verdict'] for r in rows] == ['Accepted']

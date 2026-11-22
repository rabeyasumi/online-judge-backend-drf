
import pytest

from helpers import submit
from submissions.judge import JudgeServiceError
from submissions.models import Submission

pytestmark = pytest.mark.django_db

TWO_CASES = (('1 2', '3'), ('2 3', '5'))


@pytest.fixture
def problem(make_problem):
    return make_problem(cases=TWO_CASES)


def test_accepted(client, student, problem, fake_judge):
    fake_judge.outputs = {'1 2': '3', '2 3': '5'}

    response = submit(client, problem)

    assert response.status_code == 201
    body = response.json()
    assert body['verdict'] == 'Accepted'
    assert body['passed_testcases'] == 2
    assert body['total_testcases'] == 2
    assert body['problem_id'] == problem.id
    assert body['execution_time'] == pytest.approx(0.02)   
    assert body['memory'] == 1000                          

    saved = Submission.objects.get(pk=body['submission_id'])
    assert saved.student == student
    assert saved.element == problem
    assert saved.verdict == 'Accepted'
    assert saved.language == 'python3'
    assert saved.code == 'print(3)'


def test_compiles_once_then_runs_each_test_case(client, problem, fake_judge):
    fake_judge.outputs = {'1 2': '3', '2 3': '5'}

    submit(client, problem)

    assert len(fake_judge.compile_calls) == 1
    assert [c['stdin'] for c in fake_judge.run_calls] == ['1 2', '2 3']
    assert fake_judge.calls[0]['compile_only'] is True     


def test_whitespace_differences_are_ignored(client, make_problem, fake_judge):
    problem = make_problem(cases=(('1', '1\n2\n3\n'),))
    fake_judge.outputs = {'1': '  1 2   3 '}

    assert submit(client, problem).json()['verdict'] == 'Accepted'


def test_wrong_answer_stops_at_first_mismatch(client, make_problem, fake_judge):
    problem = make_problem(cases=(('a', '1'), ('b', '2'), ('c', '3')))
    fake_judge.outputs = {'a': '1', 'b': 'WRONG', 'c': '3'}

    body = submit(client, problem).json()

    assert body['verdict'] == 'Wrong Answer'
    assert body['passed_testcases'] == 1
    assert body['total_testcases'] == 3
    assert len(fake_judge.run_calls) == 2                   
    assert Submission.objects.get(pk=body['submission_id']).verdict == 'Wrong Answer'


def test_wrong_answer_on_the_first_case(client, problem, fake_judge):
    fake_judge.default_output = 'nope'

    body = submit(client, problem).json()

    assert body['verdict'] == 'Wrong Answer'
    assert body['passed_testcases'] == 0


def test_compilation_error_skips_test_cases(client, problem, fake_judge):
    fake_judge.compile_status = '1'
    fake_judge.compile_output = 'main.py: SyntaxError'

    response = submit(client, problem, code='print(')

    assert response.status_code == 201
    body = response.json()
    assert body['verdict'] == 'Compilation Error'
    assert body['compiler_output'] == 'main.py: SyntaxError'
    assert body['passed_testcases'] == 0
    assert body['total_testcases'] == 2
    assert body['execution_time'] is None
    assert fake_judge.run_calls == []
    assert Submission.objects.get(pk=body['submission_id']).verdict == 'Compilation Error'


def test_unknown_compilation_status_is_a_judge_error(client, problem, fake_judge):
    fake_judge.compile_status = None        

    body = submit(client, problem).json()

    assert body['verdict'] == 'Judge Error'
    assert fake_judge.run_calls == []


def test_judge_down_during_compile_is_a_judge_error(client, problem, fake_judge):
    fake_judge.compile_error = JudgeServiceError('JDoodle timed out')

    response = submit(client, problem)

    assert response.status_code == 201
    body = response.json()
    assert body['verdict'] == 'Judge Error'
    assert body['passed_testcases'] == 0
    assert Submission.objects.get(pk=body['submission_id']).verdict == 'Judge Error'


def test_judge_down_in_the_middle_keeps_the_partial_count(client, problem, fake_judge):
    fake_judge.outputs = {'1 2': '3', '2 3': '5'}
    fake_judge.run_errors = {2: JudgeServiceError('daily limit reached')}

    body = submit(client, problem).json()

    assert body['verdict'] == 'Judge Error'
    assert body['passed_testcases'] == 1


def test_malformed_judge_result_is_a_judge_error(client, problem, fake_judge):
    fake_judge.broken_run_result = True      

    body = submit(client, problem).json()

    assert body['verdict'] == 'Judge Error'


def test_every_submission_is_stored_with_its_own_row(client, problem, fake_judge):
    fake_judge.outputs = {'1 2': '3', '2 3': '5'}

    first = submit(client, problem).json()['submission_id']
    second = submit(client, problem).json()['submission_id']

    assert first != second
    assert Submission.objects.count() == 2

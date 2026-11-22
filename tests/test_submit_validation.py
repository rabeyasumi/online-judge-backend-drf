
import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import Student

from helpers import submit
from submissions.models import Submission

URL = '/api/submissions/'
pytestmark = pytest.mark.django_db


def assert_not_judged(fake_judge):
    assert fake_judge.calls == []
    assert Submission.objects.count() == 0


def test_requires_login(anon_client, make_problem, fake_judge):
    problem = make_problem()
    response = submit(anon_client, problem)
    assert response.status_code == 401
    assert_not_judged(fake_judge)


@pytest.mark.parametrize('missing', ['problem_id', 'language', 'code'])
def test_each_required_field_is_checked(client, make_problem, fake_judge, missing):
    problem = make_problem()
    payload = {'problem_id': problem.id, 'language': 'python3', 'code': 'print(3)'}
    del payload[missing]
    response = client.post(URL, payload, format='json')
    assert response.status_code == 400
    assert_not_judged(fake_judge)


@pytest.mark.parametrize('code', ['', '   \n  ', 12345, None, ['print(1)']])
def test_code_must_be_a_non_empty_string(client, make_problem, fake_judge, code):
    problem = make_problem()
    response = submit(client, problem, code=code)
    assert response.status_code == 400
    assert_not_judged(fake_judge)


def test_problem_id_must_be_a_number(client, fake_judge):
    response = client.post(
        URL, {'problem_id': 'abc', 'language': 'python3', 'code': 'x'}, format='json'
    )
    assert response.status_code == 400
    assert_not_judged(fake_judge)


def test_unsupported_language_is_rejected(client, make_problem, fake_judge):
    problem = make_problem()
    response = submit(client, problem, language='brainfuck')
    assert response.status_code == 400
    assert 'language' in response.json()['error'].lower()
    assert_not_judged(fake_judge)


def test_unknown_problem_returns_404(client, fake_judge):
    response = client.post(
        URL, {'problem_id': 999999, 'language': 'python3', 'code': 'x'}, format='json'
    )
    assert response.status_code == 404
    assert_not_judged(fake_judge)


def test_problem_without_test_cases_is_rejected(client, make_problem, fake_judge):
    problem = make_problem(cases=())
    response = submit(client, problem)
    assert response.status_code == 400
    assert 'test case' in response.json()['error'].lower()
    assert_not_judged(fake_judge)


def test_user_without_student_profile_is_forbidden(make_problem, fake_judge):
    User = get_user_model()
    user = User.objects.create_user('nostudent', 'n@example.com', 'StrongPass123!')
    Student.objects.filter(user=user).delete()
    token = Token.objects.create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    response = submit(client, make_problem())
    assert response.status_code == 403
    assert_not_judged(fake_judge)


import itertools
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import Student
from contests.models import Contest
from problems.models import Element
from problems.models import TestCase as ProblemTestCase   # alias: pytest must not collect it
from submissions import views as submission_views
from submissions.judge import JudgeServiceError

User = get_user_model()
_n = itertools.count(1)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _required_extras(model, given, n):
  
    values = {}
    for field in model._meta.concrete_fields:
        if field.primary_key or field.name in given or field.is_relation:
            continue
        needs = field.unique or not (field.has_default() or field.null or field.blank)
        if not needs:
            continue
        kind = field.get_internal_type()
        if kind in ('CharField', 'TextField', 'SlugField'):
            values[field.name] = f'{field.name}-{n}'
        elif kind in ('IntegerField', 'BigIntegerField', 'PositiveIntegerField', 'SmallIntegerField'):
            values[field.name] = 1 if not field.unique else n
        elif kind in ('FloatField', 'DecimalField'):
            values[field.name] = 1
        elif kind == 'BooleanField':
            values[field.name] = False
    return values


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------

@pytest.fixture
def make_student(db):
    def _make(handle=None, password='StrongPass123!'):
        n = next(_n)
        handle = handle or f'user{n}'
        user = User.objects.create_user(
            username=handle, email=f'{handle}@example.com', password=password
        )
        student, _ = Student.objects.update_or_create(
            user=user,
            defaults={'name': handle.title(), 'handle': handle},
        )
        return student
    return _make


@pytest.fixture
def make_client():
    """Return an APIClient logged in as the given student (token auth)."""
    def _make(student):
        token, _ = Token.objects.get_or_create(user=student.user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        return client
    return _make


@pytest.fixture
def student(make_student):
    return make_student('alice')


@pytest.fixture
def client(student, make_client):
    return make_client(student)


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def make_contest(db):
    """Contest whose window is given in minutes relative to now."""
    def _make(start_min=-30, end_min=60, is_rated=False, name=None):
        now = timezone.now()
        n = next(_n)
        return Contest.objects.create(
            cname=name or f'Contest {n}',
            tag='test',
            start_datetime=now + timedelta(minutes=start_min),
            end_datetime=now + timedelta(minutes=end_min),
            is_rated=is_rated,
        )
    return _make


@pytest.fixture
def make_problem(db):
    """Problem with test cases. `cases` is a list of (input, expected_output)."""
    def _make(contest=None, rating=1000, cases=(('1 2', '3'),), **extra):
        n = next(_n)
        data = dict(
            pname=f'Problem {n}', description='desc', author='admin',
            category='math', rating=rating,
        )
        data.update(extra)
        field_names = {f.name for f in Element._meta.get_fields()}
        if contest is not None and 'contest' in field_names:
            data['contest'] = contest
        data.update(_required_extras(Element, data, n))
        problem = Element.objects.create(**data)
        if contest is not None and 'contest' not in field_names and 'contests' in field_names:
            problem.contests.add(contest)       
        for stdin, expected in cases:
            ProblemTestCase.objects.create(
                problem=problem, input_data=stdin, expected_output=expected
            )
        return problem
    return _make


# ---------------------------------------------------------------------------
# Fake JDoodle
# ---------------------------------------------------------------------------

class FakeJudge:
    """Stands in for submissions.judge.execute_code.

    Configure it in a test, then inspect `.calls` to see what the view asked.
    """

    def __init__(self):
        self.calls = []
        self.compile_status = '0'        
        self.compile_output = ''
        self.compile_error = None         
        self.outputs = {}                 
        self.default_output = ''
        self.cpu_time = '0.01'
        self.memory = '1000'
        self.run_errors = {}               
        self.broken_run_result = False    
        self._runs = 0

    def __call__(self, code, language, stdin='', compile_only=False):
        self.calls.append(
            {'code': code, 'language': language, 'stdin': stdin, 'compile_only': compile_only}
        )
        if compile_only:
            if self.compile_error:
                raise self.compile_error
            return {
                'output': self.compile_output, 'execution_time': None,
                'memory': None, 'compilation_status': self.compile_status,
            }
        self._runs += 1
        if self._runs in self.run_errors:
            raise self.run_errors[self._runs]
        if self.broken_run_result:
            return {'execution_time': None, 'memory': None}
        return {
            'output': self.outputs.get(stdin, self.default_output),
            'execution_time': self.cpu_time, 'memory': self.memory,
            'compilation_status': self.compile_status,
        }

    @property
    def compile_calls(self):
        return [c for c in self.calls if c['compile_only']]

    @property
    def run_calls(self):
        return [c for c in self.calls if not c['compile_only']]


@pytest.fixture
def fake_judge(monkeypatch):
    judge = FakeJudge()
    monkeypatch.setattr(submission_views, 'execute_code', judge)
    return judge


@pytest.fixture
def judge_down():
    return JudgeServiceError('JDoodle is down')

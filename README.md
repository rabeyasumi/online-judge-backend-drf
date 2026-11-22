[![CI Status](https://github.com/rabeyasumi/online-judge-backend-drf/actions/workflows/ci.yml/badge.svg)](https://github.com/rabeyasumi/online-judge-backend-drf/actions/workflows/ci.yml)

# Globe Online Judge: Backend

REST API for a competitive programming platform where students solve problems, join timed contests and follow live standings.

**Live site:** https://online-judge-phi.vercel.app

## Features

- Token-based authentication with student profiles
- Problems with hidden test cases, filtering and search
- Code submission judged through the JDoodle API (compile check, then every test case)
- Verdicts: Accepted, Wrong Answer, Compilation Error, Judge Error
- Timed contests with live standings
- ICPC-style penalty (AC minutes + 20 per wrong attempt)
- Per-problem score: `max(0.4 x rating, rating - 0.004 x rating x minutes - 50 x wrong)`
- Global rating that updates after rated contests: `new = old + 0.3 x (score - old)`
- Rating history and global standings
- Submission lists with filters (own submissions and all submissions)

## Tech stack

Python, Django, Django REST Framework, PostgreSQL, Token Authentication, JDoodle API, pytest, GitHub Actions

## API overview

| Endpoint | Description |
|---|---|
| `POST /api/submissions/` | Submit code for a problem (login required) |
| `GET /api/submissions/my/` | Your submissions (`?problem_id=`, `?contest=`) |
| `GET /api/submissions/all/` | All submissions (`?verdict=`, `?language=`, `?contest_id=`, `?problem_name=`, `?handle=`) |
| `GET /api/submissions/languages/` | Supported languages |
| `GET /api/contests/<id>/standings/` | Contest standings |
| `GET /api/problems/` | Problem list (`?search=`, `?rating=`, `?category=`) |

## Run locally

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Create a `.env` file in this folder:

```
DJANGO_SECRET_KEY=your-secret-key
JDOODLE_CLIENT_ID=your-client-id
JDOODLE_CLIENT_SECRET=your-client-secret
```

## Tests

The submission API has 64 tests. The JDoodle judge is replaced with a fake one, so tests run offline and need no API keys.

```
pip install -r requirements-dev.txt
pytest
pytest --cov=submissions
```

| Test file | Covers |
|---|---|
| `test_scoring_units.py` | Score and rating formulas |
| `test_languages_api.py` | Language list endpoint |
| `test_submit_validation.py` | Authentication and input validation |
| `test_submit_verdicts.py` | Judging flow and every verdict |
| `test_submit_contest.py` | Contest scoring, penalty and standings |
| `test_submission_lists.py` | Submission lists, filters and code visibility |

Tests run automatically on every push and pull request with GitHub Actions.

## Data model

11 relational tables: User, Student, Contest, Element (problem), TestCase, Submission, Standings, GlobalStanding, RatingChange, ProfileSubmissionStatistics and FavProblem.
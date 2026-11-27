"""Settings used only by pytest.

Our normal settings with three overrides: an in-memory SQLite database
(fast, needs no PostgreSQL), a fast password hasher, and fake JDoodle keys.
No test ever calls the real JDoodle API.
"""
from .settings import *  # noqa: F401,F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

JDOODLE_CLIENT_ID = 'test-id'
JDOODLE_CLIENT_SECRET = 'test-secret'
